"""Tests for the 20-question Phase 3 baseline RAG accuracy benchmark."""

from backend.intelligence.evaluation.baseline_20q import (
    BASELINE_CATEGORIES,
    Baseline20QBenchmarkRunner,
    build_baseline_20q_dataset,
)


def test_baseline_20q_dataset_has_all_required_categories():
    dataset = build_baseline_20q_dataset()
    assert len(dataset) == 20
    categories = {case.category for case in dataset}
    for required in BASELINE_CATEGORIES:
        assert required in categories
    unanswerable = [c for c in dataset if c.is_unanswerable]
    assert len(unanswerable) == 3


def test_baseline_20q_runner_executes_and_records_metrics():
    runner = Baseline20QBenchmarkRunner()
    report = runner.run(flag_overrides={}, profile_name="baseline")
    assert report.profile == "baseline"
    assert report.total_questions == 20
    assert len(report.results) == 20
    assert 0.0 <= report.mean_recall_at_5 <= 1.0
    assert 0.0 <= report.mean_mrr <= 1.0
    assert 0.0 <= report.citation_accuracy <= 1.0
    assert report.mean_latency_ms >= 0.0
    for item in report.results:
        assert item.generated_answer
        assert item.response_latency_ms >= 0.0
