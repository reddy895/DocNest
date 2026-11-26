"""Unified Query Intelligence Engine combining classification, rewriting, and expansion."""

from typing import Dict, List, Optional
from backend.intelligence.contracts import QueryAnalysis, QueryIntent
from backend.intelligence.query_intelligence.classifier import QueryClassifier
from backend.intelligence.query_intelligence.rewriter import ConversationQueryRewriter
from backend.intelligence.query_intelligence.expander import QueryExpander


class QueryIntelligenceEngine:
    """Orchestrates query classification, context resolution, expansion, and decomposition."""

    def __init__(
        self,
        classifier: Optional[QueryClassifier] = None,
        rewriter: Optional[ConversationQueryRewriter] = None,
        expander: Optional[QueryExpander] = None,
    ):
        self.classifier = classifier or QueryClassifier()
        self.rewriter = rewriter or ConversationQueryRewriter()
        self.expander = expander or QueryExpander()

    def analyze(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        selected_doc_ids: Optional[List[str]] = None,
        selected_doc_names: Optional[List[str]] = None,
    ) -> QueryAnalysis:
        original = (question or "").strip()
        if not original:
            return QueryAnalysis(original_query="", resolved_query="", intent=QueryIntent.FACTUAL)

        intent, is_follow_up, is_multi_doc = self.classifier.classify(
            original, chat_history=chat_history, selected_doc_ids=selected_doc_ids
        )

        needs_rewrite = self.rewriter.needs_rewrite(original, chat_history=chat_history)
        resolved = (
            self.rewriter.resolve_locally(
                original, chat_history=chat_history, selected_doc_names=selected_doc_names
            )
            if needs_rewrite
            else original
        )

        expanded_terms = (
            [] if intent == QueryIntent.CONVERSATIONAL else self.expander.expand(resolved)
        )
        sub_queries = (
            self.expander.decompose(resolved)
            if is_multi_doc or intent == QueryIntent.COMPARATIVE
            else [resolved]
        )

        return QueryAnalysis(
            original_query=original,
            resolved_query=resolved,
            intent=intent,
            expanded_terms=expanded_terms,
            sub_queries=sub_queries,
            is_multi_document=is_multi_doc,
            is_follow_up=is_follow_up,
            needs_rewriting=needs_rewrite,
            referenced_docs=list(selected_doc_ids or []),
        )

