"""Citation Verification Engine ensuring every cited source exists in retrieved evidence."""

import re
from typing import List, Tuple
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

