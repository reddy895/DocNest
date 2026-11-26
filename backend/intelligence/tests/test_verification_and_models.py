"""Unit & integration tests for Context, Model Compatibility, Verification, and Orchestrator."""

import pytest

from backend.intelligence.contracts import AnswerStyle, RetrievedPassage
from backend.intelligence.context_optimizer.engine import ContextOptimizationEngine
from backend.intelligence.context_optimizer.prompt_templates import build_system_prompt
from backend.intelligence.model_compatibility.manager import (
    EmbeddingCollectionMismatchError,
    ModelCompatibilityManager,
)
from backend.intelligence.model_compatibility.openai_adapter import OpenAICompatibleAdapter
from backend.intelligence.citation_verification.aligner import ClaimSourceAligner
from backend.intelligence.answer_verification.verifier import AnswerVerifier
from backend.intelligence.answer_verification.policy import BoundedVerificationPolicy
from backend.intelligence.evaluation.benchmark_dataset import build_benchmark_dataset
from backend.intelligence.evaluation.runner import BenchmarkRunner


def _passages():
    return [
        RetrievedPassage(
            chunk_id="fin_1",
            doc_id="doc_fin",
            filename="Quarterly_Report.pdf",
            page_number=2,
            chunk_index=0,
            section_heading="Revenue",
            text="Q3 revenue reached $48.2 million with a 19.4% year-over-year increase.",
            rerank_score=0.92,
            final_score=0.92,
        ),
        RetrievedPassage(
            chunk_id="fin_2",
            doc_id="doc_fin",
            filename="Quarterly_Report.pdf",
            page_number=2,
            chunk_index=1,
            section_heading="Revenue",
            text="Enterprise subscriptions drove the majority of Q3 revenue growth.",
            rerank_score=0.85,
            final_score=0.85,
        ),
    ]


def test_context_optimization_budget_and_styles():
    passages = _passages()
    engine = ContextOptimizationEngine()
    ctx = engine.optimize("What was Q3 revenue?", passages, token_budget=500, style=AnswerStyle.TECHNICAL)
    assert len(ctx.passages) == 2
    assert "Quarterly_Report.pdf, p. 2" in ctx.formatted_context
    assert ctx.total_tokens_estimated <= 500

    # Tight budget drops lower-priority chunks
    tight = engine.optimize("What was Q3 revenue?", passages, token_budget=45)
    assert len(tight.passages) == 1
    assert tight.dropped_count == 1

    for style in AnswerStyle:
        sys_prompt = build_system_prompt(style)
        assert "[Filename, p. X]" in sys_prompt


@pytest.mark.asyncio
async def test_model_compatibility_and_embedding_guard():
    mgr = ModelCompatibilityManager()

    qwen = mgr.inspect_model("qwen2.5:7b")
    assert qwen.family == "qwen"
    assert qwen.context_window == 32768
    assert qwen.supports_tools is True

    gemma = mgr.inspect_model("gemma2:9b")
    assert gemma.family == "gemma"
    assert gemma.supports_tools is False

    embed = mgr.inspect_model("nomic-embed-text")
    assert embed.is_embedding_model is True
    assert embed.supports_streaming is False

    with pytest.raises(EmbeddingCollectionMismatchError):
        mgr.validate_embedding_change("bge-m3", "docnest_collection")

    # Unconfigured OpenAI adapter fails gracefully on health check
    oai = OpenAICompatibleAdapter(base_url="", api_key="")
    health = await oai.check_health()
    assert health.available is False


def test_citation_verification_and_alignment():
    passages = _passages()
    aligner = ClaimSourceAligner(min_alignment=0.20)

    good_answer = "Q3 revenue reached $48.2 million with 19.4% growth [Quarterly_Report.pdf, p. 2]."
    good_res = aligner.verify_and_align(good_answer, passages)
    assert len(good_res) == 1
    assert good_res[0].is_valid is True

    fake_answer = "Q3 revenue reached $99.9 million [NonExistent.pdf, p. 9]."
    fake_res = aligner.verify_and_align(fake_answer, passages)
    assert len(fake_res) == 1
    assert fake_res[0].is_valid is False


@pytest.mark.asyncio
async def test_answer_verifier_and_bounded_retry_policy():
    passages = _passages()
    verifier = AnswerVerifier(min_faithfulness=0.35, min_relevance=0.20)

    faithful = verifier.verify(
        "What was Q3 revenue?",
        "Q3 revenue reached $48.2 million with a 19.4% increase from enterprise subscriptions.",
        passages,
    )
    assert faithful.is_faithful is True
    assert faithful.needs_retry is False

    calls = 0

    async def always_hallucinate():
        nonlocal calls
        calls += 1
        return "The CEO flew to Mars in a purple submarine in 1999."

    policy = BoundedVerificationPolicy(verifier=verifier, max_retries=1)
    final_ans, res, attempts = await policy.execute("What was Q3 revenue?", passages, always_hallucinate)
    assert attempts == 2  # 1 initial + 1 bounded retry
    assert res.abstained is True
    assert "could not find sufficient verified evidence" in final_ans.lower()


def test_benchmark_dataset_and_runner():
    dataset = build_benchmark_dataset()
    assert len(dataset) >= 100
    categories = {c.category for c in dataset}
    assert len(categories) == 10

    runner = BenchmarkRunner()
    reports = runner.run_all_profiles()
    assert len(reports) == 6
    assert all(r.total_cases == len(dataset) for r in reports)

