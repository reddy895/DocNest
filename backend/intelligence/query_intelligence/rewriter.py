"""Conversation context resolution and follow-up query rewriting."""

import re
from typing import Dict, List, Optional


class ConversationQueryRewriter:
    """
    Resolves coreferences and implicit references from recent chat history
    only when rewriting is actually needed, avoiding unnecessary distortion.
    """

    PRONOUN_RE = re.compile(
        r"\b(it|its|they|them|their|theirs|this|that|these|those|the\s+above|earlier)\b",
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
        if len(text.split()) <= 4 and text.lower().startswith(("what about", "and ", "why ", "how ")):
            return True
        return False

    def resolve_locally(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        selected_doc_names: Optional[List[str]] = None,
    ) -> str:
        """
        Deterministic context-preserving resolution using recent user/assistant topics
        and active document names without making unsupported assumptions.
        """
        text = (query or "").strip()
        if not self.needs_rewrite(text, chat_history):
            return text

        # Extract the most recent substantive user topic from history
        recent_user_turns = [
            (m.get("text") or m.get("content") or "").strip()
            for m in (chat_history or [])
            if (m.get("sender") or m.get("role")) == "user"
        ]
        recent_user_turns = [t for t in recent_user_turns if t and t.lower() != text.lower()]

        context_hints: List[str] = []
        if recent_user_turns:
            prev_topic = recent_user_turns[-1]
            # Keep it concise to avoid diluting embeddings
            context_hints.append(prev_topic[:120])

        if selected_doc_names:
            doc_str = ", ".join(selected_doc_names[:3])
            context_hints.append(f"in {doc_str}")

        if not context_hints:
            return text

        return f"{text} (context: {' '.join(context_hints)})"
