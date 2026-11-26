"""Configurable grounded answer prompt templates across 5 answer styles."""

from typing import Dict
from backend.intelligence.contracts import AnswerStyle


STYLE_DIRECTIVES: Dict[AnswerStyle, str] = {
    AnswerStyle.CONCISE: (
        "Provide a brief, direct answer using bullet points. Focus strictly on the highest-signal facts."
    ),
    AnswerStyle.DETAILED: (
        "Provide a thorough, well-structured answer with clear headings and supporting details from the context."
    ),
    AnswerStyle.TECHNICAL: (
        "Provide a precise technical explanation preserving exact parameters, formulas, architectures, and measurements."
    ),
    AnswerStyle.RESEARCH: (
        "Adopt a scholarly, analytical tone. Distinguish empirical facts from interpretations and highlight any contradictions across documents."
    ),
    AnswerStyle.BEGINNER: (
        "Explain concepts in plain, accessible language. Define technical terms briefly using only context-supported meanings."
    ),
}


def build_system_prompt(style: AnswerStyle = AnswerStyle.DETAILED) -> str:
    directive = STYLE_DIRECTIVES.get(style, STYLE_DIRECTIVES[AnswerStyle.DETAILED])
    return (
        "You are DocNest, a factual document intelligence assistant.\n"
        "GROUNDING RULES:\n"
        "1. Answer strictly using the retrieved CONTEXT PASSAGES.\n"
        "2. Cite every factual claim inline as [Filename, p. X].\n"
        "3. Preserve exact numbers, dates, and measurements.\n"
        "4. Identify contradictions if sources disagree.\n"
        "5. If evidence is insufficient, state honestly that the uploaded documents do not contain enough information.\n"
        "6. Never expose private chain-of-thought reasoning or fabricate citations.\n"
        f"STYLE INSTRUCTION: {directive}"
    )


def build_user_prompt(question: str, formatted_context: str) -> str:
    return (
        f"CONTEXT PASSAGES:\n{formatted_context}\n\n"
        f"USER QUESTION:\n{question}\n\n"
        "ANSWER:"
    )
