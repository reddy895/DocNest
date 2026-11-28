"""Tests for Phase 9 Citation Verification: source/page validation and Citation schema compatibility."""

from backend.app.models.schemas import Citation
from backend.intelligence.citation_verification.verifier import CitationVerifier
from backend.intelligence.contracts import RetrievedPassage


def test_citation_verifier_rejects_guessed_pages_and_preserves_schema():
    passages = [
        RetrievedPassage(
            chunk_id="chunk_fin_1",
            doc_id="doc_fin",
            filename="Quarterly_Financial_Report.pdf",
            page_number=1,
            chunk_index=0,
            text="Q3 total revenue reached $48.2 million.",
            final_score=0.88,
        )
    ]
    answer = (
        "Q3 revenue was $48.2 million [Quarterly_Financial_Report.pdf, p. 1]. "
        "Net income doubled [Quarterly_Financial_Report.pdf, p. 99]. "
        "Also see [Unknown_Doc.pdf, p. 2]."
    )

    verifier = CitationVerifier()
    raw_results = verifier.verify_answer_citations(answer, passages)
    assert len(raw_results) == 3
    assert raw_results[0].is_valid is True
    assert raw_results[1].is_valid is False
    assert raw_results[2].is_valid is False

    formatted = verifier.verify_and_format_citations(answer, passages)
    assert len(formatted) == 1
    cit = Citation(**formatted[0])
    assert cit.source_id == "chunk_fin_1"
    assert cit.filename == "Quarterly_Financial_Report.pdf"
    assert cit.page_number == 1
