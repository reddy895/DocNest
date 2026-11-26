"""Conservative domain query expansion and complex query decomposition."""

import re
from typing import Dict, List


class QueryExpander:
    """Expands technical terminology and decomposes comparative/multi-part questions."""

    SYNONYM_MAP: Dict[str, List[str]] = {
        "rag": ["retrieval augmented generation", "hybrid search"],
        "llm": ["large language model", "ollama"],
        "accuracy": ["precision", "recall", "f1", "benchmark"],
        "latency": ["response time", "ms", "throughput"],
        "methodology": ["approach", "method", "architecture"],
        "findings": ["results", "conclusions", "outcomes"],
        "revenue": ["income", "earnings", "financial"],
        "compliance": ["policy", "regulation", "audit"],
        "security": ["authentication", "authorization", "encryption"],
    }

    SPLIT_RE = re.compile(r"\s+(?:and\s+also|and\s+how|and\s+what|vs\.?|versus)\s+", re.IGNORECASE)

    def expand(self, query: str, max_terms: int = 4) -> List[str]:
        tokens = re.findall(r"[a-zA-Z0-9_-]+", (query or "").lower())
        expanded: List[str] = []
        seen = set(tokens)
        for tok in tokens:
            for syn in self.SYNONYM_MAP.get(tok, []):
                if syn not in seen:
                    expanded.append(syn)
                    seen.add(syn)
                if len(expanded) >= max_terms:
                    return expanded
        return expanded

    def decompose(self, query: str) -> List[str]:
        text = (query or "").strip()
        if not text:
            return []

        parts = [p.strip(" ?.") for p in self.SPLIT_RE.split(text) if p.strip(" ?.")]
        if len(parts) > 1:
            return parts[:4]

        # Decompose comparative questions like "Compare X and Y"
        comp_match = re.match(
            r"^(?:compare|contrast)\s+(.+?)\s+(?:and|with)\s+(.+?)(?:\s+on\s+(.+))?$",
            text,
            re.IGNORECASE,
        )
        if comp_match:
            left = comp_match.group(1).strip(" ?.")
            right = comp_match.group(2).strip(" ?.")
            aspect = (comp_match.group(3) or "").strip(" ?.")
            suffix = f" regarding {aspect}" if aspect else ""
            return [f"{left}{suffix}", f"{right}{suffix}"]

        return [text]
