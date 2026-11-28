"""Citation Verification Engine ensuring every cited source exists in retrieved evidence."""

import re
from typing import Any, Dict, List, Tuple
from backend.intelligence.contracts import RetrievedPassage, VerifiedCitation


CITATION_PATTERN = re.compile(
    r"\[([^\[\],]+?),\s*(?:p\.|Page)\s*(\d+)\]",
    re.IGNORECASE,
)


def parse_inline_citations(answer_text: str) -> List[Tuple[str, int]]:
    """Extract (filename, page_number) pairs from [Filename, p. X] inline citations."""
    matches: List[Tuple[str, int]] = []
    for match in CITATION_PATTERN.finditer(answer_text or ""):
        fname = match.group(1).strip()
        try:
            page = int(match.group(2))
        except ValueError:
            page = -1
        matches.append((fname, page))
    return matches


class CitationVerifier:
    """Validates inline citations against actually retrieved passages."""

    @staticmethod
    def _match_passage(
        filename: str,
        page_number: int,
        passages: List[RetrievedPassage],
    ) -> RetrievedPassage | None:
        target = filename.lower().strip()
        for p in passages:
            p_name = p.filename.lower().strip()
            if (p_name == target or target in p_name or p_name in target) and p.page_number == page_number:
                return p
        return None

    def verify_answer_citations(
        self,
        answer_text: str,
        retrieved_passages: List[RetrievedPassage],
    ) -> List[VerifiedCitation]:
        parsed = parse_inline_citations(answer_text)
        results: List[VerifiedCitation] = []

        for fname, page in parsed:
            if page < 1:
                results.append(
                    VerifiedCitation(
                        filename=fname,
                        page_number=page,
                        is_valid=False,
                        reason="Invalid page number (< 1).",
                    )
                )
                continue

            matched = self._match_passage(fname, page, retrieved_passages)
            if matched is None:
                results.append(
                    VerifiedCitation(
                        filename=fname,
                        page_number=page,
                        is_valid=False,
                        reason="Cited document/page was not present in retrieved passages.",
                    )
                )
            else:
                results.append(
                    VerifiedCitation(
                        doc_id=matched.doc_id,
                        filename=matched.filename,
                        page_number=matched.page_number,
                        chunk_id=matched.chunk_id,
                        is_valid=True,
                        alignment_score=1.0,
                    )
                )

        return results

    def verify_and_format_citations(
        self,
        answer_text: str,
        retrieved_passages: List[RetrievedPassage],
    ) -> List[Dict[str, Any]]:
        """
        Verify inline citations against retrieved passages and return only verified
        citations formatted to match backend.app.models.schemas.Citation.
        """
        verified = self.verify_answer_citations(answer_text, retrieved_passages)
        passage_by_chunk = {p.chunk_id: p for p in retrieved_passages if p.chunk_id}
        seen_keys: set[Tuple[str, int]] = set()
        formatted: List[Dict[str, Any]] = []

        for item in verified:
            if not item.is_valid or not item.chunk_id:
                continue
            passage = passage_by_chunk.get(item.chunk_id)
            if passage is None or not passage.text.strip():
                continue
            key = (passage.chunk_id, passage.page_number)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            raw_score = (
                passage.rerank_score
                if passage.rerank_score is not None
                else (passage.final_score or passage.dense_score or 0.5)
            )
            clamped_score = max(0.0, min(1.0, float(raw_score)))
            formatted.append(
                {
                    "source_id": passage.chunk_id,
                    "filename": passage.filename,
                    "page_number": passage.page_number,
                    "chunk_index": passage.chunk_index,
                    "content": passage.text,
                    "relevance_score": round(clamped_score, 4),
                }
            )
        return formatted

