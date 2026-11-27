"""Module 3: Bounded 10-Stage Multi-Stage Retrieval & Evidence-Verified Generation."""

import time
from typing import Awaitable, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.intelligence.contracts import (
    AnswerDepth,
    ClaimVerificationItem,
    CompletenessReport,
    EvidenceSufficiencyResult,
    OptimizedContext,
    QueryAnalysis,
    RetrievedPassage,
    VerifiedCitation,
)
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.query_intelligence.engine import QueryIntelligenceEngine
from backend.intelligence.project_intelligence.engine import ProjectAnalysis, ProjectIntelligenceEngine
from backend.intelligence.hybrid_retrieval.engine import HybridRetrievalEngine
from backend.intelligence.reranking.engine import RerankingEngine
from backend.intelligence.context_optimizer.engine import ContextOptimizationEngine
from backend.intelligence.context_optimizer.depth_controls import (
    build_depth_aware_prompt,
    resolve_answer_depth,
)
from backend.intelligence.answer_verification.evidence_grounding import (
    EvidenceSufficiencyChecker,
    build_missing_evidence_response,
    build_strict_evidence_system_prompt,
)
from backend.intelligence.answer_verification.claim_verifier import ClaimLevelVerifier
from backend.intelligence.answer_verification.completeness import AnswerCompletenessChecker
from backend.intelligence.citation_verification.aligner import ClaimSourceAligner


class MultiStageResult(BaseModel):
    answer: str
    depth: AnswerDepth
    query_analysis: QueryAnalysis
    project_analysis: ProjectAnalysis
    sufficiency: EvidenceSufficiencyResult
    context: OptimizedContext
    citations: List[VerifiedCitation] = Field(default_factory=list)
    claims: List[ClaimVerificationItem] = Field(default_factory=list)
    completeness: Optional[CompletenessReport] = None
    extra_retrieval_triggered: bool = False
    total_latency_ms: float = 0.0


class MultiStagePipeline:
    """
    Executes the bounded 10-stage retrieval, evidence sufficiency check,
    depth-controlled generation, and claim-level verification pipeline.
    """

    def __init__(
        self,
        flags: Optional[FeatureFlagManager] = None,
        query_engine: Optional[QueryIntelligenceEngine] = None,
        project_engine: Optional[ProjectIntelligenceEngine] = None,
        retrieval_engine: Optional[HybridRetrievalEngine] = None,
        reranking_engine: Optional[RerankingEngine] = None,
        context_engine: Optional[ContextOptimizationEngine] = None,
        sufficiency_checker: Optional[EvidenceSufficiencyChecker] = None,
        claim_verifier: Optional[ClaimLevelVerifier] = None,
        citation_aligner: Optional[ClaimSourceAligner] = None,
        completeness_checker: Optional[AnswerCompletenessChecker] = None,
        max_latency_ms: float = 15000.0,
    ):
        self.flags = flags or FeatureFlagManager()
        self.query_engine = query_engine or QueryIntelligenceEngine()
        self.project_engine = project_engine or ProjectIntelligenceEngine()
        self.retrieval_engine = retrieval_engine or HybridRetrievalEngine()
        self.reranking_engine = reranking_engine or RerankingEngine(use_cross_encoder=False)
        self.context_engine = context_engine or ContextOptimizationEngine()
        self.sufficiency_checker = sufficiency_checker or EvidenceSufficiencyChecker()
        self.claim_verifier = claim_verifier or ClaimLevelVerifier()
        self.citation_aligner = citation_aligner or ClaimSourceAligner()
        self.completeness_checker = completeness_checker or AnswerCompletenessChecker()
        self.max_latency_ms = max_latency_ms

    async def run(
        self,
        question: str,
        generate_fn: Callable[[str, str], Awaitable[str]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        doc_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        requested_depth: Optional[AnswerDepth] = None,
        top_k: int = 8,
    ) -> MultiStageResult:
        t_start = time.perf_counter()
        active = self.flags.as_dict()

        # Stage 1: Understand question & classify intent
        qa = self.query_engine.analyze(
            question, chat_history=chat_history, selected_doc_ids=doc_ids
        )
        proj = (
            self.project_engine.analyze_project_query(qa.resolved_query)
            if active.get("ENABLE_PROJECT_INTELLIGENCE", True)
            else ProjectAnalysis()
        )
        depth = resolve_answer_depth(
            requested_depth=requested_depth,
            is_project_query=proj.is_project_query,
            recommended_depth=proj.recommended_depth,
        )

        # Stage 2 & 3: Identify target sections & retrieve passages
        sub_queries = list(dict.fromkeys(qa.sub_queries + proj.section_queries))
        effective_k = max(top_k, 10) if proj.is_project_query else top_k
        passages = self.retrieval_engine.retrieve(
            query=qa.resolved_query,
            expanded_terms=qa.expanded_terms,
            sub_queries=sub_queries[:5],
            top_k=max(effective_k * 2, 16),
            doc_ids=doc_ids,
            workspace_id=workspace_id,
        )

        # Stage 4: Rerank passages
        reranked = self.reranking_engine.rerank(
            query=qa.resolved_query, passages=passages, top_k=effective_k, min_score=0.05
        )

        # Stage 5: Identify missing information & section gaps
        sufficiency = self.sufficiency_checker.check(qa.resolved_query, reranked)
        if proj.is_project_query:
            proj = self.project_engine.inspect_section_coverage(proj, reranked)

        # Stage 6: Bounded additional retrieval if missing information
        extra_triggered = False
        elapsed_ms = (time.perf_counter() - t_start) * 1000
        if (
            (sufficiency.needs_additional_retrieval or proj.missing_target_sections)
            and elapsed_ms < self.max_latency_ms * 0.6
        ):
            extra_queries = (
                [f"{qa.resolved_query} {sec}" for sec in proj.missing_target_sections[:2]]
                if proj.missing_target_sections
                else [f"{qa.resolved_query} {' '.join(sufficiency.missing_aspects[:3])}"]
            )
            extra_raw = self.retrieval_engine.retrieve(
                query=qa.resolved_query,
                sub_queries=extra_queries,
                top_k=effective_k,
                doc_ids=doc_ids,
                workspace_id=workspace_id,
            )
            if extra_raw:
                extra_triggered = True
                merged_map = {p.chunk_id: p for p in reranked}
                for ep in extra_raw:
                    merged_map.setdefault(ep.chunk_id, ep)
                reranked = self.reranking_engine.rerank(
                    query=qa.resolved_query,
                    passages=list(merged_map.values()),
                    top_k=effective_k,
                    min_score=0.05,
                )
                sufficiency = self.sufficiency_checker.check(qa.resolved_query, reranked)
                if proj.is_project_query:
                    proj = self.project_engine.inspect_section_coverage(proj, reranked)

        # If evidence remains insufficient, return honest limitation without fabricating
        if active.get("ENABLE_EVIDENCE_GROUNDING", True) and not sufficiency.is_sufficient:
            msg = build_missing_evidence_response(question, sufficiency.missing_aspects)
            total_ms = round((time.perf_counter() - t_start) * 1000, 2)
            return MultiStageResult(
                answer=msg,
                depth=depth,
                query_analysis=qa,
                project_analysis=proj,
                sufficiency=sufficiency,
                context=OptimizedContext(passages=reranked),
                extra_retrieval_triggered=extra_triggered,
                total_latency_ms=total_ms,
            )

        # Stage 7: Build structured evidence context
        budget = 4000 if depth == AnswerDepth.COMPREHENSIVE_PROJECT else 2500
        opt_ctx = self.context_engine.optimize(
            qa.resolved_query, reranked, token_budget=budget
        )

        # Stage 8: Generate answer
        sys_prompt = build_strict_evidence_system_prompt()
        usr_prompt = build_depth_aware_prompt(
            question=question,
            formatted_context=opt_ctx.formatted_context,
            depth=depth,
            missing_sections=proj.missing_target_sections if proj.is_project_query else None,
        )
        raw_answer = await generate_fn(usr_prompt, sys_prompt)

        # Stage 9 & 10: Claim-level verification, citation check, completeness check
        claims = (
            self.claim_verifier.verify_answer(raw_answer, opt_ctx.passages)
            if active.get("ENABLE_CLAIM_VERIFICATION", True)
            else []
        )
        citations = self.citation_aligner.verify_and_align(raw_answer, opt_ctx.passages)
        completeness = (
            self.completeness_checker.evaluate(
                raw_answer, proj.documented_sections_found, opt_ctx.passages
            )
            if proj.is_project_query
            else None
        )

        total_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return MultiStageResult(
            answer=raw_answer,
            depth=depth,
            query_analysis=qa,
            project_analysis=proj,
            sufficiency=sufficiency,
            context=opt_ctx,
            citations=citations,
            claims=claims,
            completeness=completeness,
            extra_retrieval_triggered=extra_triggered,
            total_latency_ms=total_ms,
        )

