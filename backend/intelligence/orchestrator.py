"""Isolated Intelligence Engine 2.0 orchestrator with strict feature-flag gating."""

import time
from typing import Any, Dict, List, Optional, Tuple
from backend.intelligence.contracts import (
    AnswerStyle,
    AnswerVerificationResult,
    IntelligenceTrace,
    OptimizedContext,
    QueryAnalysis,
    QueryIntent,
    RetrievedPassage,
)
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.adapters.base import execute_with_fallback
from backend.intelligence.adapters.existing_rag_adapter import (
    ExistingOllamaAdapter,
    ExistingRerankerAdapter,
    ExistingRetrieverAdapter,
)


class IntelligenceOrchestrator:
    """
    Coordinates optional AI Intelligence 2.0 stages around the existing RAG pipeline.
    When all flags are False (default), delegates directly to existing adapters.
    """

    def __init__(
        self,
        flag_manager: Optional[FeatureFlagManager] = None,
        retriever_adapter: Optional[ExistingRetrieverAdapter] = None,
        reranker_adapter: Optional[ExistingRerankerAdapter] = None,
        llm_adapter: Optional[ExistingOllamaAdapter] = None,
        query_engine: Optional[Any] = None,
        hybrid_engine: Optional[Any] = None,
        reranking_engine: Optional[Any] = None,
        context_engine: Optional[Any] = None,
        citation_verifier: Optional[Any] = None,
        answer_verifier: Optional[Any] = None,
        project_engine: Optional[Any] = None,
    ):
        self.flags = flag_manager or FeatureFlagManager()
        self.base_retriever = retriever_adapter or ExistingRetrieverAdapter()
        self.base_reranker = reranker_adapter or ExistingRerankerAdapter()
        self.base_llm = llm_adapter or ExistingOllamaAdapter()

        self.query_engine = query_engine
        self.hybrid_engine = hybrid_engine
        self.reranking_engine = reranking_engine
        self.context_engine = context_engine
        self.citation_verifier = citation_verifier
        self.answer_verifier = answer_verifier
        self.project_engine = project_engine

    def prepare_retrieval_and_context(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        doc_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.30,
        style: AnswerStyle = AnswerStyle.DETAILED,
    ) -> Tuple[QueryAnalysis, OptimizedContext, IntelligenceTrace]:
        """Run query intelligence, retrieval, reranking, and context optimization safely."""
        active = self.flags.as_dict()
        trace = IntelligenceTrace(flags_active=active)
        fallback_reasons: List[str] = []

        # 1. Query Intelligence
        t0 = time.perf_counter()
        baseline_qa = QueryAnalysis(
            original_query=question,
            resolved_query=question,
            intent=QueryIntent.FACTUAL,
        )
        if active.get("ENABLE_QUERY_INTELLIGENCE") and self.query_engine is not None:
            qa = execute_with_fallback(
                "query_intelligence",
                lambda: self.query_engine.analyze(
                    question=question,
                    chat_history=chat_history,
                    selected_doc_ids=doc_ids,
                ),
                lambda: baseline_qa,
                fallback_reasons,
            )
        else:
            qa = baseline_qa
        trace.query_analysis = qa
        trace.timings_ms["query_intelligence_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # 1b. Deep Project Understanding (multi-section retrieval targeting)
        pa = None
        project_queries: List[str] = []
        if (
            active.get("ENABLE_PROJECT_UNDERSTANDING") or active.get("ENABLE_PROJECT_INTELLIGENCE")
        ) and self.project_engine is not None:
            pa = execute_with_fallback(
                "project_understanding",
                lambda: self.project_engine.analyze_project_query(qa.resolved_query),
                lambda: None,
                fallback_reasons,
            )
            trace.project_analysis = pa
            if pa is not None and getattr(pa, "is_project_query", False):
                project_queries = list(getattr(pa, "section_queries", []) or [])

        # 2. Retrieval (Hybrid Enhancement or Baseline)
        t1 = time.perf_counter()
        if active.get("ENABLE_HYBRID_SEARCH") and self.hybrid_engine is not None:
            passages = execute_with_fallback(
                "hybrid_retrieval",
                lambda: self.hybrid_engine.retrieve(
                    query=qa.resolved_query,
                    expanded_terms=qa.expanded_terms,
                    sub_queries=project_queries or qa.sub_queries,
                    top_k=max(top_k * 4, 20),
                    doc_ids=doc_ids,
                    workspace_id=workspace_id,
                ),
                lambda: self.base_retriever.retrieve(
                    query=qa.resolved_query,
                    top_k=max(top_k * 4, 20),
                    doc_ids=doc_ids,
                    workspace_id=workspace_id,
                ),
                fallback_reasons,
            )
        elif project_queries:
            seen_ids = set()
            passages = []
            for pq in [qa.resolved_query] + project_queries[:6]:
                for item in self.base_retriever.retrieve(
                    query=pq,
                    top_k=max(top_k * 2, 10),
                    doc_ids=doc_ids,
                    workspace_id=workspace_id,
                ):
                    if item.chunk_id not in seen_ids:
                        seen_ids.add(item.chunk_id)
                        passages.append(item)
            passages = passages[: max(top_k * 4, 20)]
        else:
            passages = self.base_retriever.retrieve(
                query=qa.resolved_query,
                top_k=max(top_k * 4, 20),
                doc_ids=doc_ids,
                workspace_id=workspace_id,
            )
        trace.retrieval_count = len(passages)
        trace.timings_ms["retrieval_ms"] = round((time.perf_counter() - t1) * 1000, 2)

        # 3. Reranking
        t2 = time.perf_counter()
        if active.get("ENABLE_RERANKING") and self.reranking_engine is not None:
            reranked = execute_with_fallback(
                "reranking",
                lambda: self.reranking_engine.rerank(
                    query=qa.resolved_query,
                    passages=passages,
                    top_k=top_k,
                    min_score=min_score,
                ),
                lambda: self.base_reranker.rerank(
                    query=qa.resolved_query,
                    passages=passages,
                    top_k=top_k,
                    min_score=min_score,
                ),
                fallback_reasons,
            )
        else:
            reranked = passages[:top_k]
        trace.reranked_count = len(reranked)
        trace.timings_ms["reranking_ms"] = round((time.perf_counter() - t2) * 1000, 2)

        if pa is not None and hasattr(self.project_engine, "inspect_section_coverage"):
            trace.project_analysis = self.project_engine.inspect_section_coverage(pa, reranked)

        # 4. Context Optimization
        t3 = time.perf_counter()
        if active.get("ENABLE_CONTEXT_OPTIMIZATION") and self.context_engine is not None:
            opt_ctx = execute_with_fallback(
                "context_optimization",
                lambda: self.context_engine.optimize(
                    query=qa.resolved_query,
                    passages=reranked,
                    style=style,
                ),
                lambda: OptimizedContext(passages=reranked, style=style),
                fallback_reasons,
            )
        else:
            opt_ctx = OptimizedContext(passages=reranked, style=style)
        trace.context_tokens = opt_ctx.total_tokens_estimated
        trace.timings_ms["context_optimization_ms"] = round((time.perf_counter() - t3) * 1000, 2)

        trace.fallback_triggered = len(fallback_reasons) > 0
        trace.fallback_reasons = fallback_reasons
        return qa, opt_ctx, trace

    def verify_response(
        self,
        question: str,
        answer: str,
        passages: List[RetrievedPassage],
        trace: IntelligenceTrace,
    ) -> Tuple[List[Any], AnswerVerificationResult]:
        """Run optional citation and answer verification."""
        active = trace.flags_active
        citations_res: List[Any] = []
        answer_res = AnswerVerificationResult()

        if active.get("ENABLE_CITATION_VERIFICATION") and self.citation_verifier is not None:
            citations_res = execute_with_fallback(
                "citation_verification",
                lambda: self.citation_verifier.verify_answer_citations(answer, passages),
                lambda: [],
                trace.fallback_reasons,
            )
            trace.citation_verification = citations_res

        if active.get("ENABLE_ANSWER_VERIFICATION") and self.answer_verifier is not None:
            answer_res = execute_with_fallback(
                "answer_verification",
                lambda: self.answer_verifier.verify(question, answer, passages),
                lambda: AnswerVerificationResult(),
                trace.fallback_reasons,
            )
            trace.answer_verification = answer_res

        trace.fallback_triggered = len(trace.fallback_reasons) > 0
        return citations_res, answer_res

