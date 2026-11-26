"""Module 5: Multi-turn conversation context resolution and follow-up query rewriting."""

import re
from typing import Dict, List, Optional


class ConversationQueryRewriter:
    """
    Resolves coreferences and implicit project/entity references across multi-turn
    conversation history (e.g., 'Explain the architecture' -> 'What database is used?'
    -> 'Why was it selected?'), avoiding unnecessary distortion on standalone queries.
    """

    PRONOUN_RE = re.compile(
        r"\b(it|its|they|them|their|theirs|this|that|these|those|the\s+above|earlier|same)\b",
        re.IGNORECASE,
    )
    IMPLICIT_FOLLOWUP_RE = re.compile(
        r"^(what|which|why|how|where|when|who)\b.{0,45}\b(used|selected|chosen|implemented|stored|handled|configured|worked|achieved)\b",
        re.IGNORECASE,
    )

    def needs_rewrite(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> bool:
        if not chat_history or len(chat_history) == 0:
            return False
        text = (query or "").strip()
        if not text:
            return False
        if self.PRONOUN_RE.search(text):
            return True
        if self.IMPLICIT_FOLLOWUP_RE.search(text):
            return True
        if len(text.split()) <= 5 and text.lower().startswith(("what about", "and ", "why ", "how ")):
            return True
        return False

    @staticmethod
    def _extract_turn_text(turn: Dict[str, str]) -> str:
        return (turn.get("text") or turn.get("content") or "").strip()

    @staticmethod
    def _extract_turn_role(turn: Dict[str, str]) -> str:
        return (turn.get("sender") or turn.get("role") or "").lower()

    def resolve_locally(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        selected_doc_names: Optional[List[str]] = None,
    ) -> str:
        """
        Resolve ambiguous follow-ups using both the active project/topic anchor from
        earlier user turns and the most recent assistant entity context.
        """
        text = (query or "").strip()
        if not self.needs_rewrite(text, chat_history):
            return text

        history = chat_history or []
        user_turns = [
            self._extract_turn_text(m)
            for m in history
            if self._extract_turn_role(m) == "user"
        ]
        user_turns = [t for t in user_turns if t and t.lower() != text.lower()]

        assistant_turns = [
            self._extract_turn_text(m)
            for m in history
            if self._extract_turn_role(m) == "assistant"
        ]
        assistant_turns = [t for t in assistant_turns if t]

        context_parts: List[str] = []
        # Include earlier anchor topic (e.g., project/architecture) + immediate prior user turn
        if user_turns:
            if len(user_turns) > 1:
                context_parts.append(user_turns[0][:80])
            context_parts.append(user_turns[-1][:100])

        # If pronoun likely refers to an entity mentioned in the last assistant reply (e.g. "PostgreSQL", "ChromaDB")
        if self.PRONOUN_RE.search(text) and assistant_turns:
            last_ans = assistant_turns[-1][:140]
            context_parts.append(last_ans)

        if selected_doc_names:
            context_parts.append(f"in {', '.join(selected_doc_names[:3])}")

        if not context_parts:
            return text

        deduped_context = " | ".join(dict.fromkeys(context_parts))
        return f"{text} (context: {deduped_context})"
