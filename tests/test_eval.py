import pytest
from backend.app.services.eval_dataset import get_benchmark_dataset, EvalTestCase
from backend.app.services.eval_judge import LLMJudge
from backend.app.services.eval_runner import calculate_context_precision, compute_percentiles


def test_benchmark_dataset_loading():
    dataset = get_benchmark_dataset()
    assert len(dataset) >= 6
    assert all(isinstance(case, EvalTestCase) for case in dataset)

    # Filtered limit
    partial = get_benchmark_dataset(limit=2)
    assert len(partial) == 2


def test_judge_json_score_parsing():
    judge = LLMJudge()

    # 1. Clean JSON
    clean_json = '{"score": 0.95, "reasoning": "Direct evidence found"}'
    parsed1 = judge._parse_json_score(clean_json)
    assert parsed1["score"] == 0.95
    assert parsed1["reasoning"] == "Direct evidence found"

    # 2. Markdown fenced JSON
    fenced_json = """Here is my evaluation:
```json
{
  "claims": ["Rev was $142.8M"],
  "score": 0.88,
  "reasoning": "Fully factual"
}
```
"""
    parsed2 = judge._parse_json_score(fenced_json)
    assert parsed2["score"] == 0.88

    # 3. Malformed JSON with regex score fallback
    malformed = 'The evaluation gave a "score": 0.72 with some claims missing.'
    parsed3 = judge._parse_json_score(malformed)
    assert parsed3["score"] == 0.72


def test_context_precision_ranking():
    # Target doc: report.pdf
    # Case 1: Target doc is at rank 1 -> higher precision
    high_rank_chunks = [
        {"filename": "report.pdf", "page_number": 1},
        {"filename": "other.pdf", "page_number": 1},
    ]
    p_high = calculate_context_precision(high_rank_chunks, target_doc="report.pdf")

    # Case 2: Target doc is at rank 2 -> lower precision
    low_rank_chunks = [
        {"filename": "other.pdf", "page_number": 1},
        {"filename": "report.pdf", "page_number": 1},
    ]
    p_low = calculate_context_precision(low_rank_chunks, target_doc="report.pdf")

    assert p_high > p_low
    assert p_high == 1.0
    assert p_low == 0.5


def test_latency_percentile_computation():
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    p = compute_percentiles(latencies)

    assert p["avg"] == 55.0
    assert p["p50"] == 55.0
    assert p["p90"] == 91.0
    assert p["p95"] == 95.5

    # Empty list edge case
    empty_p = compute_percentiles([])
    assert empty_p["avg"] == 0.0
