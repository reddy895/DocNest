"""Independent 20-question baseline evaluation suite for DocNest RAG (Phase 3)."""

import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.intelligence.contracts import AnswerStyle, RetrievedPassage
from backend.intelligence.evaluation.benchmark_dataset import CORPUS_PASSAGES, BenchmarkCase
from backend.intelligence.evaluation.metrics import (
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
    summarize_latencies,
)
from backend.intelligence.evaluation.runner import _InMemoryCorpusAdapter
from backend.intelligence.feature_flags.manager import FeatureFlagManager
from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.intelligence.citation_verification.verifier import CitationVerifier


BASELINE_CATEGORIES = (
    "direct_factual",
    "technical",
    "project_explanation",
    "architecture",
    "multi_document",
    "missing_information",
)


class Baseline20QCaseResult(BaseModel):
    case_id: str
    category: str
    question: str
    generated_answer: str
    retrieved_chunk_ids: List[str] = Field(default_factory=list)
    retrieval_recall_at_5: float = 0.0
    retrieval_precision_at_5: float = 0.0
    retrieval_mrr: float = 0.0
    citation_correctness: float = 1.0
    response_latency_ms: float = 0.0
    unsupported_claims: List[str] = Field(default_factory=list)


class Baseline20QReport(BaseModel):
    profile: str = "baseline"
    total_questions: int = 20
    category_counts: Dict[str, int] = Field(default_factory=dict)
    mean_recall_at_5: float = 0.0
    mean_precision_at_5: float = 0.0
    mean_mrr: float = 0.0
    citation_accuracy: float = 1.0
    unsupported_claim_rate: float = 0.0
    mean_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    results: List[Baseline20QCaseResult] = Field(default_factory=list)


def build_baseline_20q_dataset() -> List[BenchmarkCase]:
    """
    Build 20 representative questions across 6 categories using verified passages
    in CORPUS_PASSAGES without altering any production documents.
    """
    return [
        # 1. Direct factual (4)
        BenchmarkCase(
            case_id="b20_01",
            category="direct_factual",
            question="What was Q3 total revenue and year-over-year growth?",
            expected_answer="$48.2 million with 19.4% year-over-year increase.",
            relevant_chunk_ids=["fin_p1_c0"],
        ),
        BenchmarkCase(
            case_id="b20_02",
            category="direct_factual",
            question="What is the Cloud AI segment operating margin in Q3?",
            expected_answer="28.5% operating margin on $31.0M revenue.",
            relevant_chunk_ids=["fin_p2_c1"],
        ),
        BenchmarkCase(
            case_id="b20_03",
            category="direct_factual",
            question="What is the document retention period in the compliance policy?",
            expected_answer="365 days.",
            relevant_chunk_ids=["comp_p1_c0"],
        ),
        BenchmarkCase(
            case_id="b20_04",
            category="direct_factual",
            question="What is the median CPU latency of the Cross-Encoder reranker?",
            expected_answer="42ms median CPU latency.",
            relevant_chunk_ids=["ai_p3_c2"],
        ),
        # 2. Technical (4)
        BenchmarkCase(
            case_id="b20_05",
            category="technical",
            question="Which embedding model and vector dimension are used in ChromaDB?",
            expected_answer="nomic-embed-text with 768 dimensions.",
            relevant_chunk_ids=["ai_p1_c0"],
        ),
        BenchmarkCase(
            case_id="b20_06",
            category="technical",
            question="Which reranker model and abstention threshold are configured?",
            expected_answer="ms-marco-MiniLM-L-6-v2 with a 0.30 abstention threshold.",
            relevant_chunk_ids=["ai_p3_c2"],
        ),
        BenchmarkCase(
            case_id="b20_07",
            category="technical",
            question="How does the compliance policy protect uploaded documents?",
            expected_answer="Local storage with SHA-256 deduplication, path traversal sanitization, and workspace-level isolation.",
            relevant_chunk_ids=["comp_p1_c0"],
        ),
        BenchmarkCase(
            case_id="b20_08",
            category="technical",
            question="What Reciprocal Rank Fusion parameter k is used to combine dense and sparse search?",
            expected_answer="k=60.",
            relevant_chunk_ids=["ai_p1_c0"],
        ),
        # 3. Project explanation (3)
        BenchmarkCase(
            case_id="b20_09",
            category="project_explanation",
            question="Explain the overall RAG retrieval and reranking workflow in this project.",
            expected_answer="Combines ChromaDB dense embeddings and BM25Okapi sparse search via RRF (k=60), followed by Cross-Encoder reranking.",
            relevant_chunk_ids=["ai_p1_c0", "ai_p3_c2"],
        ),
        BenchmarkCase(
            case_id="b20_10",
            category="project_explanation",
            question="Summarize the Q3 financial performance across Cloud AI and On-Prem segments.",
            expected_answer="Total revenue $48.2M (+19.4% YoY); Cloud AI $31.0M at 28.5% margin, On-Prem $17.2M at 22.1% margin.",
            relevant_chunk_ids=["fin_p1_c0", "fin_p2_c1"],
        ),
        BenchmarkCase(
            case_id="b20_11",
            category="project_explanation",
            question="Explain how security and retention are enforced in the document platform.",
            expected_answer="SHA-256 deduplication, path traversal sanitization, workspace isolation, and 365-day retention.",
            relevant_chunk_ids=["comp_p1_c0"],
        ),
        # 4. Architecture (3)
        BenchmarkCase(
            case_id="b20_12",
            category="architecture",
            question="Describe the hybrid retrieval architecture combining dense and sparse search.",
            expected_answer="ChromaDB dense embeddings (nomic-embed-text, 768d) merged with BM25Okapi via RRF (k=60).",
            relevant_chunk_ids=["ai_p1_c0"],
        ),
        BenchmarkCase(
            case_id="b20_13",
            category="architecture",
            question="How does the reranking stage integrate into the retrieval architecture?",
            expected_answer="Evaluates top-20 candidates with ms-marco-MiniLM-L-6-v2 and enforces a 0.30 abstention threshold.",
            relevant_chunk_ids=["ai_p3_c2"],
        ),
        BenchmarkCase(
            case_id="b20_14",
            category="architecture",
            question="What storage and isolation layers exist in the architecture?",
            expected_answer="Local document storage with workspace-level ownership isolation and ChromaDB vector store.",
            relevant_chunk_ids=["comp_p1_c0", "ai_p1_c0"],
        ),
        # 5. Multi-document (3)
        BenchmarkCase(
            case_id="b20_15",
            category="multi_document",
            question="Compare the financial performance in the financial report with the AI architecture latency metrics.",
            expected_answer="Q3 revenue was $48.2M (Cloud AI 28.5% margin), while Cross-Encoder reranking runs in 42ms median CPU latency.",
            relevant_chunk_ids=["fin_p1_c0", "fin_p2_c1", "ai_p3_c2"],
        ),
        BenchmarkCase(
            case_id="b20_16",
            category="multi_document",
            question="Across both the AI whitepaper and compliance manual, how are documents indexed and protected?",
            expected_answer="Indexed via nomic-embed-text in ChromaDB and BM25Okapi, protected with SHA-256 deduplication and workspace isolation.",
            relevant_chunk_ids=["ai_p1_c0", "comp_p1_c0"],
        ),
        BenchmarkCase(
            case_id="b20_17",
            category="multi_document",
            question="How do the Cloud AI segment metrics relate to the hybrid RAG technology stack?",
            expected_answer="Cloud AI generated $31.0M at 28.5% margin alongside the ChromaDB + BM25 + MiniLM RAG pipeline.",
            relevant_chunk_ids=["fin_p2_c1", "ai_p1_c0", "ai_p3_c2"],
        ),
        # 6. Missing-information (3)
        BenchmarkCase(
            case_id="b20_18",
            category="missing_information",
            question="What was the CEO's exact compensation bonus in Q3?",
            expected_answer="Not specified in the uploaded documents.",
            relevant_chunk_ids=[],
            is_unanswerable=True,
        ),
        BenchmarkCase(
            case_id="b20_19",
            category="missing_information",
            question="What Kubernetes cluster autoscaling limits are configured in production?",
            expected_answer="Not specified in the uploaded documents.",
            relevant_chunk_ids=[],
            is_unanswerable=True,
        ),
        BenchmarkCase(
            case_id="b20_20",
            category="missing_information",
            question="What F1 accuracy score did the model achieve on the SQuAD v2 dataset?",
            expected_answer="Not specified in the uploaded documents.",
            relevant_chunk_ids=[],
            is_unanswerable=True,
        ),
    ]


def _synthesize_baseline_answer(case: BenchmarkCase, passages: List[RetrievedPassage]) -> str:
    """Deterministic extractive baseline answer formatter simulating existing prompt grounding."""
    if not passages:
        return "I could not find sufficient evidence in the uploaded documents to answer this question."
    snippets = [f"{p.text} [{p.filename}, p. {p.page_number}]" for p in passages[:2]]
    return " ".join(snippets)


class Baseline20QBenchmarkRunner:
    """Runs the 20-question evaluation in baseline (all flags False) or custom flag mode."""

    def __init__(self, corpus: Optional[List[RetrievedPassage]] = None):
        self.corpus = corpus or CORPUS_PASSAGES
        self.citation_verifier = CitationVerifier()

    def run(
        self,
        flag_overrides: Optional[Dict[str, bool]] = None,
        profile_name: str = "baseline",
    ) -> Baseline20QReport:
        dataset = build_baseline_20q_dataset()
        flags = FeatureFlagManager(overrides=flag_overrides or {})
        mem_adapter = _InMemoryCorpusAdapter(corpus=self.corpus)

        orchestrator = IntelligenceOrchestrator(
            flag_manager=flags,
            retriever_adapter=mem_adapter,
        )

        results: List[Baseline20QCaseResult] = []
        latencies: List[float] = []
        recalls: List[float] = []
        precisions: List[float] = []
        mrrs: List[float] = []
        citation_scores: List[float] = []
        unsupported_cases = 0
        cat_counts: Dict[str, int] = {}

        for case in dataset:
            cat_counts[case.category] = cat_counts.get(case.category, 0) + 1
            t0 = time.perf_counter()
            _, opt_ctx, _ = orchestrator.prepare_retrieval_and_context(
                question=case.question,
                chat_history=case.chat_history,
                doc_ids=case.doc_ids,
                top_k=5,
                min_score=0.15,
                style=AnswerStyle.DETAILED,
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
            latencies.append(elapsed_ms)

            passages = opt_ctx.passages
            retrieved_ids = [p.chunk_id for p in passages]
            relevant = set(case.relevant_chunk_ids)

            if case.is_unanswerable:
                r5 = 1.0 if not retrieved_ids else 0.0
                p5 = 1.0 if not retrieved_ids else 0.0
                mrr = 1.0 if not retrieved_ids else 0.0
            else:
                r5 = recall_at_k(retrieved_ids, relevant, k=5)
                p5 = precision_at_k(retrieved_ids, relevant, k=5)
                mrr = mean_reciprocal_rank(retrieved_ids, relevant)

            recalls.append(r5)
            precisions.append(p5)
            mrrs.append(mrr)

            answer = _synthesize_baseline_answer(case, passages)
            verified_cits = self.citation_verifier.verify_answer_citations(answer, passages)
            if verified_cits:
                cit_ok = sum(1 for c in verified_cits if c.is_valid) / len(verified_cits)
            else:
                cit_ok = 1.0 if case.is_unanswerable else 0.0
            citation_scores.append(cit_ok)

            unsupported: List[str] = []
            if case.is_unanswerable and passages:
                unsupported.append("Retrieved unrelated passages for missing-information query.")
                unsupported_cases += 1

            results.append(
                Baseline20QCaseResult(
                    case_id=case.case_id,
                    category=case.category,
                    question=case.question,
                    generated_answer=answer,
                    retrieved_chunk_ids=retrieved_ids,
                    retrieval_recall_at_5=round(r5, 4),
                    retrieval_precision_at_5=round(p5, 4),
                    retrieval_mrr=round(mrr, 4),
                    citation_correctness=round(cit_ok, 4),
                    response_latency_ms=elapsed_ms,
                    unsupported_claims=unsupported,
                )
            )

        n = max(len(dataset), 1)
        lat_summary = summarize_latencies(latencies)
        return Baseline20QReport(
            profile=profile_name,
            total_questions=len(dataset),
            category_counts=cat_counts,
            mean_recall_at_5=round(sum(recalls) / n, 4),
            mean_precision_at_5=round(sum(precisions) / n, 4),
            mean_mrr=round(sum(mrrs) / n, 4),
            citation_accuracy=round(sum(citation_scores) / n, 4),
            unsupported_claim_rate=round(unsupported_cases / n, 4),
            mean_latency_ms=lat_summary["mean_ms"],
            p95_latency_ms=lat_summary["p95_ms"],
            results=results,
        )
