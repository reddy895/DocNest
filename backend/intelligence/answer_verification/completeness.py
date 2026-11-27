"""Module 7: Answer Completeness Checker for broad project and multi-section queries."""

from typing import List
from backend.intelligence.contracts import CompletenessReport, RetrievedPassage
from backend.intelligence.project_intelligence.engine import SECTION_KEYWORDS


class AnswerCompletenessChecker:
    """
    Evaluates whether a broad project answer covers the documented sections
    actually present in the retrieved evidence.
    """

    def evaluate(
        self,
        answer_text: str,
        documented_sections: List[str],
        passages: List[RetrievedPassage] | None = None,
    ) -> CompletenessReport:
        if not documented_sections:
            return CompletenessReport(is_complete=True, completeness_score=1.0)

        lower_ans = (answer_text or "").lower()
        covered: List[str] = []
        missing: List[str] = []

        for sec in documented_sections:
            kws = SECTION_KEYWORDS.get(sec, [sec.lower()])
            if sec.lower() in lower_ans or any(kw in lower_ans for kw in kws):
                covered.append(sec)
            else:
                missing.append(sec)

        score = round(len(covered) / len(documented_sections), 4)
        return CompletenessReport(
            is_complete=len(missing) == 0,
            completeness_score=score,
            covered_sections=covered,
            missing_documented_sections=missing,
        )

