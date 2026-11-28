"""Tests for Phase 4 Query Intelligence: classification, project detection, follow-up, and fallback."""

from backend.intelligence.contracts import QueryIntent
from backend.intelligence.query_intelligence.engine import QueryIntelligenceEngine


def test_project_question_and_followup_chain():
    engine = QueryIntelligenceEngine()
    history = [
        {"role": "user", "content": "Explain the architecture of this project."},
        {"role": "assistant", "content": "The system uses ChromaDB and BM25 with RRF."},
    ]
    qa1 = engine.analyze("Explain the architecture of this project.")
    assert qa1.original_query == "Explain the architecture of this project."
    assert qa1.intent == QueryIntent.METHODOLOGY

    qa2 = engine.analyze("Which database does it use?", chat_history=history)
    assert qa2.original_query == "Which database does it use?"
    assert qa2.is_follow_up is True
    assert qa2.needs_rewriting is True
    assert qa2.resolved_query != qa2.original_query
    assert qa2.is_project_query is True


def test_multi_document_detection_and_subqueries():
    engine = QueryIntelligenceEngine()
    qa = engine.analyze("Compare the financial report and the AI architecture whitepaper.")
    assert qa.intent == QueryIntent.COMPARATIVE
    assert qa.is_multi_document is True
    assert len(qa.sub_queries) >= 1


def test_classification_failure_falls_back_to_original_query():
    class BrokenClassifier:
        def classify(self, *args, **kwargs):
            raise RuntimeError("classifier failure")

    engine = QueryIntelligenceEngine(classifier=BrokenClassifier())  # type: ignore[arg-type]
    qa = engine.analyze("What is the Q3 revenue?")
    assert qa.original_query == "What is the Q3 revenue?"
    assert qa.resolved_query == "What is the Q3 revenue?"
    assert qa.intent == QueryIntent.FACTUAL
