"""Metadata filter engine for document, page, section, and workspace scoping."""

from typing import List, Optional
from backend.intelligence.contracts import RetrievedPassage


class MetadataFilterEngine:
    """Filters retrieved passages cleanly by doc_id, page range, section, and workspace."""

    @staticmethod
    def apply_filters(
        passages: List[RetrievedPassage],
        doc_ids: Optional[List[str]] = None,
        page_numbers: Optional[List[int]] = None,
        page_range: Optional[tuple[int, int]] = None,
        workspace_id: Optional[str] = None,
        section_query: Optional[str] = None,
    ) -> List[RetrievedPassage]:
        if not passages:
            return []

        doc_set = set(doc_ids) if doc_ids else None
        page_set = set(page_numbers) if page_numbers else None
        sec_lower = section_query.strip().lower() if section_query else None

        filtered: List[RetrievedPassage] = []
        for p in passages:
            if doc_set is not None and p.doc_id not in doc_set:
                continue
            if workspace_id and p.workspace_id != workspace_id:
                continue
            if page_set is not None and p.page_number not in page_set:
                continue
            if page_range is not None:
                lo, hi = page_range
                if not (lo <= p.page_number <= hi):
                    continue
            if sec_lower:
                heading = (p.section_heading or "").lower()
                if sec_lower not in heading:
                    continue
            filtered.append(p)

        return filtered

