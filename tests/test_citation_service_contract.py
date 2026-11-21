from backend.app.models.schemas import Citation
from backend.app.services.citation_service import enrich_and_verify_citations


def test_citation_status_uses_one_based_source_numbers():
    citations = [
        Citation(
            source_id="chunk-a",
            filename="a.pdf",
            page_number=1,
            chunk_index=0,
            content="  First source excerpt.  ",
            relevance_score=0.8,
        ),
        Citation(
            source_id="chunk-b",
            filename="b.pdf",
            page_number=2,
            chunk_index=1,
            content="Second source excerpt.",
            relevance_score=0.6,
        ),
    ]

    enriched = enrich_and_verify_citations(citations, "Evidence appears in [source 2].")

    assert [item["source_number"] for item in enriched] == [1, 2]
    assert [item["is_directly_cited"] for item in enriched] == [False, True]
    assert enriched[0]["content"] == "First source excerpt."
    assert enriched[0]["excerpt"] == "First source excerpt."
