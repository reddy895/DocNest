"""Query intent classification and complexity detection for DocNest Intelligence 2.0."""

import re
from typing import Dict, List, Optional, Tuple
from backend.intelligence.contracts import QueryIntent


class QueryClassifier:
    """Deterministic, fast classifier detecting intent, follow-ups, and multi-doc scope."""

    CONVERSATIONAL_RE = re.compile(
        r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|thanks|thank\s+you|who\s+are\s+you|what\s+can\s+you\s+do)[\s.?!]*$",
        re.IGNORECASE,
    )
    COMPARATIVE_RE = re.compile(
        r"\b(compare|comparison|contrast|difference|differences|versus|vs\.?|similarities|contradict|between\s+the\s+two)\b",
        re.IGNORECASE,
    )
    METHODOLOGY_RE = re.compile(
        r"\b(methodology|methodologies|approach|algorithm|architecture|pipeline|protocol|experimental\s+setup|design)\b",
        re.IGNORECASE,
    )
    NUMERICAL_RE = re.compile(
        r"\b(how\s+many|how\s+much|percentage|percent|ratio|average|mean|median|total|revenue|latency|accuracy|score|table|figure|metric|metrics|number)\b",
        re.IGNORECASE,
    )
    SUMMARIZATION_RE = re.compile(
        r"\b(summarize|summary|overview|key\s+takeaways|main\s+findings|tl;?dr|recap|highlights)\b",
        re.IGNORECASE,
    )
    TECHNICAL_RE = re.compile(
        r"\b(implement|implementation|code|api|endpoint|schema|function|class|sql|vector|embedding|rerank|token|parameter|config)\b",
        re.IGNORECASE,
    )
    FOLLOW_UP_RE = re.compile(
        r"\b(it|its|they|them|their|theirs|this|that|these|those|the\s+above|previous|earlier|what\s+about|elaborate|explain\s+more)\b",
        re.IGNORECASE,
    )
    MULTI_DOC_RE = re.compile(
        r"\b(documents|papers|studies|reports|files|both|all\s+sources|across\s+the)\b",
        re.IGNORECASE,
    )
    PROJECT_RE = re.compile(
        r"\b((explain|describe)\s+(the|this)\s+(entire\s+|full\s+|complete\s+)?(project|architecture|system|methodology|implementation)|project\s+(overview|architecture|methodology|objectives|limitations|scope|outcomes)|complete\s+architecture|system\s+architecture|technologies\s+used|tech\s+stack|for\s+an\s+interview|presentation)\b",
        re.IGNORECASE,
    )

    def is_project_question(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> bool:
        text = (query or "").strip()
        if not text:
            return False
        if self.PROJECT_RE.search(text):
            return True
        if chat_history and self.FOLLOW_UP_RE.search(text):
            for msg in reversed(chat_history[-4:]):
                if msg.get("role") == "user" and self.PROJECT_RE.search(msg.get("content", "")):
                    return True
        return False

    def classify(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        selected_doc_ids: Optional[List[str]] = None,
    ) -> Tuple[QueryIntent, bool, bool]:
        """
        Return (intent, is_follow_up, is_multi_document).
        """
        text = (query or "").strip()
        if not text:
            return QueryIntent.FACTUAL, False, False

        has_history = bool(chat_history and len(chat_history) > 0)
        is_follow_up = bool(has_history and self.FOLLOW_UP_RE.search(text))
        is_multi_doc = bool(
            self.MULTI_DOC_RE.search(text)
            or self.COMPARATIVE_RE.search(text)
            or (selected_doc_ids and len(selected_doc_ids) > 1)
        )

        if self.CONVERSATIONAL_RE.match(text):
            return QueryIntent.CONVERSATIONAL, False, False
        if self.COMPARATIVE_RE.search(text):
            return QueryIntent.COMPARATIVE, is_follow_up, True
        if self.SUMMARIZATION_RE.search(text):
            return QueryIntent.SUMMARIZATION, is_follow_up, is_multi_doc
        if self.METHODOLOGY_RE.search(text):
            return QueryIntent.METHODOLOGY, is_follow_up, is_multi_doc
        if self.NUMERICAL_RE.search(text):
            return QueryIntent.NUMERICAL, is_follow_up, is_multi_doc
        if self.TECHNICAL_RE.search(text):
            return QueryIntent.TECHNICAL, is_follow_up, is_multi_doc
        if is_follow_up:
            return QueryIntent.FOLLOW_UP, True, is_multi_doc

        return QueryIntent.FACTUAL, False, is_multi_doc

