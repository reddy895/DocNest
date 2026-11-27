"""Module 4: Answer Depth Controls & Structured Generation Instructions."""

from typing import Dict
from backend.intelligence.contracts import AnswerDepth


DEPTH_INSTRUCTIONS: Dict[AnswerDepth, str] = {
    AnswerDepth.BRIEF: (
        "DEPTH: Brief answer. Give a concise 2-4 sentence summary or short bullet list "
        "covering only the direct facts with citations."
    ),
    AnswerDepth.NORMAL: (
        "DEPTH: Normal explanation. Provide a clear, balanced answer with supporting evidence "
        "and inline citations."
    ),
    AnswerDepth.DETAILED: (
        "DEPTH: Detailed explanation. Explain concepts thoroughly rather than merely listing them, "
        "describe relationships between components, include documented implementation details and "
        "technical terminology, preserve exact numerical values, and organize with headings or tables."
    ),
    AnswerDepth.COMPREHENSIVE_PROJECT: (
        "DEPTH: Comprehensive project analysis. Structure the response clearly with headings for "
        "documented sections (e.g., Overview, Problem & Objectives, Architecture & Component Flow, "
        "Technologies & Their Purpose, Implementation, Results, and Documented Limitations). "
        "Include a comparison or component table where useful. Never invent missing sections; "
        "explicitly note any requested section absent from the uploaded documents."
    ),
}


def resolve_answer_depth(
    requested_depth: AnswerDepth | None = None,
    is_project_query: bool = False,
    recommended_depth: AnswerDepth = AnswerDepth.NORMAL,
) -> AnswerDepth:
    if requested_depth is not None:
        return requested_depth
    if is_project_query:
        return recommended_depth
    return AnswerDepth.NORMAL


def build_depth_aware_prompt(
    question: str,
    formatted_context: str,
    depth: AnswerDepth = AnswerDepth.NORMAL,
    missing_sections: list[str] | None = None,
) -> str:
    depth_instruction = DEPTH_INSTRUCTIONS.get(depth, DEPTH_INSTRUCTIONS[AnswerDepth.NORMAL])
    missing_note = ""
    if missing_sections:
        missing_note = (
            f"\nNOTE ON DOCUMENT COVERAGE: No passages were found for: {', '.join(missing_sections)}. "
            "Do NOT invent content for these sections; state they are not documented if asked."
        )

    return (
        f"{depth_instruction}{missing_note}\n\n"
        f"CONTEXT PASSAGES:\n{formatted_context}\n\n"
        f"USER QUESTION:\n{question}\n\n"
        "INSTRUCTIONS:\n"
        "Cite every factual claim inline as [Filename, p. X]. Avoid unnecessary repetition. "
        "Explain how technologies and components work together based strictly on the passages.\n\n"
        "ANSWER:"
    )

