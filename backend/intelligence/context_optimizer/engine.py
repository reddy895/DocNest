"""Context Optimization Engine assembling deduplicated, token-bounded, attributed context."""

from typing import List, Optional
from backend.intelligence.contracts import AnswerStyle, OptimizedContext, RetrievedPassage
from backend.intelligence.context_optimizer.budget import TokenBudgetManager
from backend.intelligence.context_optimizer.deduplicator import ContextOrganizer


class ContextOptimizationEngine:
    """Prepares clean, source-attributed context within a configurable token budget."""

    def __init__(
        self,
        budget_manager: Optional[TokenBudgetManager] = None,
        organizer: Optional[ContextOrganizer] = None,
    ):
        self.budget_manager = budget_manager or TokenBudgetManager()
        self.organizer = organizer or ContextOrganizer()

    @staticmethod
    def format_attributed_context(passages: List[RetrievedPassage]) -> str:
        blocks: List[str] = []
        for p in passages:
            sec = f" | Section: {p.section_heading}" if p.section_heading else ""
            blocks.append(
                f"--- SOURCE [{p.filename}, p. {p.page_number}{sec}] (chunk={p.chunk_id}) ---\n"
                f"{p.text.strip()}"
            )
        return "\n\n".join(blocks)

    def optimize(
        self,
        query: str,
        passages: List[RetrievedPassage],
        token_budget: Optional[int] = None,
        style: AnswerStyle = AnswerStyle.DETAILED,
    ) -> OptimizedContext:
        if not passages:
            return OptimizedContext(token_budget=token_budget or self.budget_manager.max_context_tokens, style=style)

        deduped, removed = self.organizer.deduplicate(passages)
        budgeted, tokens_used, dropped = self.budget_manager.select_within_budget(
            deduped, token_budget=token_budget
        )
        ordered = self.organizer.order_by_document_and_page(budgeted)
        formatted = self.format_attributed_context(ordered)

        return OptimizedContext(
            passages=ordered,
            formatted_context=formatted,
            total_tokens_estimated=tokens_used,
            token_budget=token_budget or self.budget_manager.max_context_tokens,
            deduplicated_count=removed,
            dropped_count=dropped,
            style=style,
        )
