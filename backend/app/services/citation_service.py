import re
from typing import List, Dict, Any, Set
from backend.app.models.schemas import Citation


def extract_cited_sources_from_text(answer_text: str) -> Set[int]:
    """
    Find source numbers referenced in the answer (e.g. '[Source 1]', '[Source 2]').
    Returns set of 1-based source indices.
    """
    pattern = re.compile(r'\[Source\s+(\d+)', re.IGNORECASE)
    matches = pattern.findall(answer_text)
    return {int(m) for m in matches if m.isdigit()}


def enrich_and_verify_citations(
    citations: List[Citation],
    answer_text: str,
) -> List[Dict[str, Any]]:
    """
    Enrich citations with explicit citation status (whether actively cited in the response text)
    and clean excerpt formatting for UI display.
    """
    cited_indices = extract_cited_sources_from_text(answer_text)

    enriched = []
    for idx, c in enumerate(citations):
        source_num = idx + 1
        is_actively_cited = source_num in cited_indices

        # Truncate clean excerpt for card preview if necessary
        clean_content = c.content.strip()
        excerpt = clean_content[:280] + ("..." if len(clean_content) > 280 else "")

        enriched.append({
            "source_number": source_num,
            "source_id": c.source_id,
            "filename": c.filename,
            "page_number": c.page_number,
            "chunk_index": c.chunk_index,
            "relevance_score": c.relevance_score,
            "relevance_percentage": int(c.relevance_score * 100),
            "content": clean_content,
            "excerpt": excerpt,
            "is_directly_cited": is_actively_cited,
        })

    return enriched
