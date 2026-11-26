"""Token estimation and configurable token budget management."""

from typing import List, Tuple
from backend.intelligence.contracts import RetrievedPassage


def estimate_tokens(text: str) -> int:
    """Fast token estimator (~1.3 tokens per word / 4 chars per token)."""
    if not text:
        return 0
    words = len(text.split())
    char_est = len(text) // 4
    return max(1, int(max(words * 1.3, char_est)))


class TokenBudgetManager:
    """Selects passages fitting within a strict token budget."""

    def __init__(self, max_context_tokens: int = 3000):
        self.max_context_tokens = max_context_tokens

    def select_within_budget(
        self,
        passages: List[RetrievedPassage],
        token_budget: int | None = None,
    ) -> Tuple[List[RetrievedPassage], int, int]:
        """
        Return (selected_passages, total_tokens_used, dropped_count).
        """
        budget = token_budget if token_budget is not None else self.max_context_tokens
        selected: List[RetrievedPassage] = []
        used = 0
        dropped = 0

        for p in passages:
            cost = estimate_tokens(p.text) + 24  # overhead for attribution header
            if used + cost <= budget:
                selected.append(p)
                used += cost
            elif not selected and budget > 80:
                # Guarantee at least one passage fits safely by trimming cleanly
                max_chars = max(120, (budget - 24) * 3)
                trimmed = p.model_copy(deep=True)
                trimmed.text = trimmed.text[:max_chars].rsplit(" ", 1)[0] + "..."
                selected.append(trimmed)
                used += estimate_tokens(trimmed.text) + 24
            else:
                dropped += 1

        return selected, used, dropped

