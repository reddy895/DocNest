"""Module 2: Deep Project Understanding — intent detection and multi-section targeting."""

import re
from typing import Dict, List, Set, Tuple
from pydantic import BaseModel, Field
from backend.intelligence.contracts import AnswerDepth, RetrievedPassage


PROJECT_SECTIONS: List[str] = [
    "Title",
    "Abstract",
    "Problem Statement",
    "Objectives",
    "Existing System",
    "Proposed System",
    "Architecture",
    "Methodology",
    "Technologies",
    "Implementation",
    "Results",
    "Limitations",
    "Future Scope",
]

SECTION_KEYWORDS: Dict[str, List[str]] = {
    "Title": ["title", "project name", "overview"],
    "Abstract": ["abstract", "summary", "introduction"],
    "Problem Statement": ["problem", "challenge", "motivation", "gap"],
    "Objectives": ["objective", "goal", "aim", "purpose"],
    "Existing System": ["existing system", "current system", "prior work", "baseline"],
    "Proposed System": ["proposed system", "solution", "our approach"],
    "Architecture": ["architecture", "diagram", "component", "module", "pipeline", "system design"],
    "Methodology": ["methodology", "algorithm", "workflow", "process", "method"],
    "Technologies": ["technology", "technologies", "tech stack", "framework", "library", "database", "model"],
    "Implementation": ["implementation", "code", "endpoint", "api", "schema", "deployment"],
    "Results": ["result", "evaluation", "benchmark", "accuracy", "performance", "outcome", "metric"],
    "Limitations": ["limitation", "constraint", "drawback", "weakness"],
    "Future Scope": ["future", "roadmap", "next step", "enhancement"],
}


class ProjectAnalysis(BaseModel):
    is_project_query: bool = False
    project_intent: str = "general"
    recommended_depth: AnswerDepth = AnswerDepth.NORMAL
    target_sections: List[str] = Field(default_factory=list)
    section_queries: List[str] = Field(default_factory=list)
    documented_sections_found: List[str] = Field(default_factory=list)
    missing_target_sections: List[str] = Field(default_factory=list)


class ProjectIntelligenceEngine:
    """
    Detects broad project/research-paper questions and orchestrates multi-section
    retrieval targets without inventing missing sections.
    """

    INTENT_PATTERNS: List[Tuple[str, re.Pattern[str], List[str], AnswerDepth]] = [
        (
            "presentation",
            re.compile(r"\b(presentation|slides|pitch|present\s+the\s+project)\b", re.I),
            ["Title", "Problem Statement", "Objectives", "Architecture", "Technologies", "Results", "Future Scope"],
            AnswerDepth.COMPREHENSIVE_PROJECT,
        ),
        (
            "interview",
            re.compile(r"\b(interview|explain.*for\s+an\s+interview|walk\s+me\s+through)\b", re.I),
            ["Title", "Problem Statement", "Architecture", "Technologies", "Implementation", "Results", "Limitations"],
            AnswerDepth.COMPREHENSIVE_PROJECT,
        ),
        (
            "complete_architecture",
            re.compile(r"\b(complete\s+architecture|system\s+architecture|full\s+architecture|architecture)\b", re.I),
            ["Proposed System", "Architecture", "Technologies", "Implementation"],
            AnswerDepth.DETAILED,
        ),
        (
            "explain_project",
            re.compile(r"\b(explain\s+(the|this)\s+project|about\s+(the|this)\s+project|entire\s+project|full\s+project)\b", re.I),
            ["Title", "Abstract", "Problem Statement", "Objectives", "Architecture", "Methodology", "Technologies", "Results", "Limitations"],
            AnswerDepth.COMPREHENSIVE_PROJECT,
        ),
        (
            "implementation",
            re.compile(r"\b(explain\s+implementation|how\s+is\s+it\s+implemented|implementation\s+details)\b", re.I),
            ["Architecture", "Technologies", "Implementation"],
            AnswerDepth.DETAILED,
        ),
        (
            "methodology",
            re.compile(r"\b(project\s+methodology|explain\s+methodology|research\s+methodology)\b", re.I),
            ["Problem Statement", "Existing System", "Proposed System", "Methodology", "Results"],
            AnswerDepth.DETAILED,
        ),
        (
            "technologies",
            re.compile(r"\b(technologies\s+used|tech\s+stack|tools\s+and\s+technologies|frameworks\s+used)\b", re.I),
            ["Technologies", "Architecture", "Implementation"],
            AnswerDepth.DETAILED,
        ),
        (
            "objectives",
            re.compile(r"\b(project\s+objectives|goals\s+of\s+the\s+project|objectives)\b", re.I),
            ["Problem Statement", "Objectives", "Proposed System"],
            AnswerDepth.NORMAL,
        ),
        (
            "outcomes",
            re.compile(r"\b(project\s+outcomes|project\s+results|findings\s+and\s+outcomes)\b", re.I),
            ["Results", "Limitations", "Future Scope"],
            AnswerDepth.DETAILED,
        ),
        (
            "limitations",
            re.compile(r"\b(project\s+limitations|limitations\s+and\s+future|drawbacks)\b", re.I),
            ["Limitations", "Future Scope"],
            AnswerDepth.NORMAL,
        ),
    ]

    def analyze_project_query(self, query: str) -> ProjectAnalysis:
        text = (query or "").strip()
        for intent_name, pattern, targets, depth in self.INTENT_PATTERNS:
            if pattern.search(text):
                sec_queries = [f"{text} {sec}" for sec in targets[:5]]
                return ProjectAnalysis(
                    is_project_query=True,
                    project_intent=intent_name,
                    recommended_depth=depth,
                    target_sections=targets,
                    section_queries=sec_queries,
                )
        return ProjectAnalysis(is_project_query=False, recommended_depth=AnswerDepth.NORMAL)

    def inspect_section_coverage(
        self,
        analysis: ProjectAnalysis,
        passages: List[RetrievedPassage],
    ) -> ProjectAnalysis:
        """Identify which target sections actually have evidence in retrieved passages."""
        if not analysis.target_sections:
            return analysis

        found: Set[str] = set()
        combined_texts = [
            f"{p.section_heading or ''} {p.text}".lower()
            for p in passages
        ]
        for sec in analysis.target_sections:
            kws = SECTION_KEYWORDS.get(sec, [sec.lower()])
            if any(any(kw in txt for kw in kws) for txt in combined_texts):
                found.add(sec)

        updated = analysis.model_copy(deep=True)
        updated.documented_sections_found = [s for s in analysis.target_sections if s in found]
        updated.missing_target_sections = [s for s in analysis.target_sections if s not in found]
        return updated
