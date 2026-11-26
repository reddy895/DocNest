"""Isolated feature flag manager for DocNest AI Intelligence Engine 2.0."""

import os
from typing import Dict, Optional
from pydantic import BaseModel


class IntelligenceFeatureFlags(BaseModel):
    """All enhancement flags default to False to preserve the existing RAG pipeline."""

    ENABLE_QUERY_INTELLIGENCE: bool = False
    ENABLE_HYBRID_SEARCH: bool = False
    ENABLE_RERANKING: bool = False
    ENABLE_CONTEXT_OPTIMIZATION: bool = False
    ENABLE_MODEL_COMPATIBILITY: bool = False
    ENABLE_CITATION_VERIFICATION: bool = False
    ENABLE_ANSWER_VERIFICATION: bool = False


def _parse_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


class FeatureFlagManager:
    """
    Reads feature flags from environment variables (supporting both ENABLE_* and
    DOCNEST_ENABLE_* prefixes) with optional per-instance overrides.
    """

    FLAG_NAMES = (
        "ENABLE_QUERY_INTELLIGENCE",
        "ENABLE_HYBRID_SEARCH",
        "ENABLE_RERANKING",
        "ENABLE_CONTEXT_OPTIMIZATION",
        "ENABLE_MODEL_COMPATIBILITY",
        "ENABLE_CITATION_VERIFICATION",
        "ENABLE_ANSWER_VERIFICATION",
    )

    def __init__(self, overrides: Optional[Dict[str, bool]] = None):
        self._overrides: Dict[str, bool] = dict(overrides or {})

    def get_flags(self) -> IntelligenceFeatureFlags:
        resolved: Dict[str, bool] = {}
        for name in self.FLAG_NAMES:
            if name in self._overrides:
                resolved[name] = bool(self._overrides[name])
                continue
            env_val = os.getenv(f"DOCNEST_{name}")
            if env_val is None:
                env_val = os.getenv(name)
            resolved[name] = _parse_bool(env_val, default=False)
        return IntelligenceFeatureFlags(**resolved)

    def is_enabled(self, flag_name: str) -> bool:
        flags = self.get_flags()
        return bool(getattr(flags, flag_name, False))

    def set_override(self, flag_name: str, value: bool) -> None:
        if flag_name not in self.FLAG_NAMES:
            raise ValueError(f"Unknown feature flag: {flag_name}")
        self._overrides[flag_name] = bool(value)

    def clear_overrides(self) -> None:
        self._overrides.clear()

    def as_dict(self) -> Dict[str, bool]:
        return self.get_flags().model_dump()
