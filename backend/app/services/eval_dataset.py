import logging
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("docnest.eval.dataset")


class EvalTestCase(BaseModel):
    id: str
    question: str
    ground_truth: str
    target_document: str
    expected_page: Optional[int] = None
    category: str = "factual"


DEFAULT_BENCHMARK_SUITE: List[EvalTestCase] = [
    EvalTestCase(
        id="eval_fin_01",
        question="What was the total consolidated revenue in Q3 2026 and what was the year-over-year growth rate?",
        ground_truth="Total consolidated revenue was $142.8 million, representing a 28.4% year-over-year growth.",
        target_document="Quarterly Financial Report Q3.pdf",
        expected_page=1,
        category="finance",
    ),
    EvalTestCase(
        id="eval_fin_02",
        question="What was the operating margin in Q3 2026 and what was the operating income?",
        ground_truth="The operating margin was 26.7% with operating income reaching $38.2 million.",
        target_document="Quarterly Financial Report Q3.pdf",
        expected_page=1,
        category="finance",
    ),
    EvalTestCase(
        id="eval_ai_01",
        question="What mathematical formula is used for Reciprocal Rank Fusion (RRF) in DocNest?",
        ground_truth="RRF(d) = SUM( 1 / (60 + rank_dense(d)) + 1 / (60 + rank_sparse(d)) ).",
        target_document="Enterprise AI Architecture Whitepaper.pdf",
        expected_page=1,
        category="architecture",
    ),
    EvalTestCase(
        id="eval_ai_02",
        question="What is the default minimum relevance score threshold below which generation halts with an abstention guardrail?",
        ground_truth="The default minimum relevance confidence threshold is 0.30.",
        target_document="Enterprise AI Architecture Whitepaper.pdf",
        expected_page=1,
        category="architecture",
    ),
    EvalTestCase(
        id="eval_sec_01",
        question="What is the maximum allowed inactivity timeout before session tokens expire under access control policy?",
        ground_truth="Session tokens expire after a maximum inactivity period of 60 minutes.",
        target_document="Corporate Compliance Policy Manual.pdf",
        expected_page=1,
        category="compliance",
    ),
    EvalTestCase(
        id="eval_sec_02",
        question="Within what timeframe must regulatory bodies be notified in writing after a data security breach?",
        ground_truth="Regulatory bodies must be notified in writing within 72 hours under GDPR Article 33 guidelines.",
        target_document="Corporate Compliance Policy Manual.pdf",
        expected_page=1,
        category="compliance",
    ),
]


def get_benchmark_dataset(limit: Optional[int] = None) -> List[EvalTestCase]:
    """Retrieve curated evaluation benchmark cases."""
    if limit:
        return DEFAULT_BENCHMARK_SUITE[:limit]
    return list(DEFAULT_BENCHMARK_SUITE)
