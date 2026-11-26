"""Automated BenchmarkRunner comparing baseline vs. enhanced Intelligence 2.0 profiles."""

import time
from typing import Dict, List, Optional
from pydantic import BaseModel

from backend.intelligence.contracts import RetrievedPassage
from backend.intelligence.evaluation.benchmark_dataset import (
    CORPUS_PASSAGES,
    BenchmarkCase,
    build_benchmark_dataset,
)
from backend.intelligence.evaluation.metrics import (
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    summarize_latencies,
)
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.hybrid_retrieval.engine import HybridRetrievalEngine
from backend.intelligence.hybrid_retrieval.normalizer import compute_keyword_score
from backend.intelligence.context_optimizer.engine import ContextOptimizationEngine
from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.intelligence.query_intelligence.engine import QueryIntelligenceEngine
from backend.intelligence.reranking.engine import RerankingEngine


class _InMemoryCorpusAdapter:
    """Deterministic in-memory retriever over CORPUS_PASSAGES for reproducible benchmarking."""

    def __init__(self, corpus: Optional[List[RetrievedPassage]] = None):
        self.corpus = corpus or CORPUS_PASSAGES

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        doc_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        search_mode: str = "hybrid",
    ) -> List[RetrievedPassage]:
        scored: List[RetrievedPassage] = []
        for p in self.corpus:
            if doc_ids and p.doc_id not in doc_ids:
                continue
            kw = compute_keyword_score(query, p.text)
            copy = p.model_copy(deep=True)
            copy.sparse_score = kw
            copy.final_score = kw
            scored.append(copy)
        scored.sort(key=lambda item: item.final_score, reverse=True)
        # Filter out zero-match passages when running unanswerable queries
        return [s for s in scored if s.final_score > 0.0][:top_k]


class ProfileBenchmarkReport(BaseModel):
    profile: str
    total_cases: int
    recall_at_5: float
    precision_at_5: float
    mrr: float
    ndcg_at_5: float
    mean_latency_ms: float
    p95_latency_ms: float


class BenchmarkRunner:
    """Runs all 6 enhancement profiles over the 110-question benchmark dataset."""

    PROFILES: Dict[str, Dict[str, bool]] = {
        "baseline": {},
        "query_intelligence": {"ENABLE_QUERY_INTELLIGENCE": True},
        "hybrid_retrieval": {"ENABLE_HYBRID_SEARCH": True},
        "reranking": {"ENABLE_RERANKING": True},
        "context_optimization": {"ENABLE_CONTEXT_OPTIMIZATION": True},
        "combined_enhancements": {
            "ENABLE_QUERY_INTELLIGENCE": True,
            "ENABLE_HYBRID_SEARCH": True,
            "ENABLE_RERANKING": True,
            "ENABLE_CONTEXT_OPTIMIZATION": True,
            "ENABLE_CITATION_VERIFICATION": True,
            "ENABLE_ANSWER_VERIFICATION": True,
        },
    }

    def run_profile(
        self,
        profile_name: str,
        cases: Optional[List[BenchmarkCase]] = None,
    ) -> ProfileBenchmarkReport:
        dataset = cases or build_benchmark_dataset()
        overrides = self.PROFILES[profile_name]
        flags = FeatureFlagManager(overrides=overrides)
        mem_adapter = _InMemoryCorpusAdapter()

        orchestrator = IntelligenceOrchestrator(
            flag_manager=flags,
            retriever_adapter=mem_adapter,
            reranker_adapter=RerankingEngine(use_cross_encoder=False),
            query_engine=QueryIntelligenceEngine(),
            hybrid_engine=HybridRetrievalEngine(base_adapter=mem_adapter),
            reranking_engine=RerankingEngine(use_cross_encoder=False),
            context_engine=ContextOptimizationEngine(),
        )

        recalls: List[float] = []
        precisions: List[float] = []
        mrrs: List[float] = []
        ndcgs: List[float] = []
        latencies: List[float] = []

        for case in dataset:
            t0 = time.perf_counter()
            _, opt_ctx, _ = orchestrator.prepare_retrieval_and_context(
                question=case.question,
                chat_history=case.chat_history,
                doc_ids=case.doc_ids,
                top_k=5,
                min_score=0.15,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed_ms)

            retrieved_ids = [p.chunk_id for p in opt_ctx.passages]
            relevant = set(case.relevant_chunk_ids)

            recalls.append(recall_at_k(retrieved_ids, relevant, k=5))
            precisions.append(precision_at_k(retrieved_ids, relevant, k=5))
            mrrs.append(mean_reciprocal_rank(retrieved_ids, relevant))
            ndcgs.append(ndcg_at_k(retrieved_ids, relevant, k=5))

        lat_summary = summarize_latencies(latencies)
        n = max(len(dataset), 1)
        return ProfileBenchmarkReport(
            profile=profile_name,
            total_cases=len(dataset),
            recall_at_5=round(sum(recalls) / n, 4),
            precision_at_5=round(sum(precisions) / n, 4),
            mrr=round(sum(mrrs) / n, 4),
            ndcg_at_5=round(sum(ndcgs) / n, 4),
            mean_latency_ms=lat_summary["mean_ms"],
            p95_latency_ms=lat_summary["p95_ms"],
        )

    def run_all_profiles(self) -> List[ProfileBenchmarkReport]:
        dataset = build_benchmark_dataset()
        return [self.run_profile(name, cases=dataset) for name in self.PROFILES]


if __name__ == "__main__":
    runner = BenchmarkRunner()
    for rep in runner.run_all_profiles():
        print(rep.model_dump_json())
