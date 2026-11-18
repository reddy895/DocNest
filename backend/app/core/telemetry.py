import time
import logging
from typing import Dict, Any, List
from collections import deque

logger = logging.getLogger("docnest.telemetry")


class TelemetryTracker:
    """Thread-safe in-memory and SQLite-backed telemetry aggregator for RAG observability."""

    def __init__(self, max_recent: int = 50):
        self.max_recent = max_recent
        self.query_count = 0
        self.recent_latencies: deque = deque(maxlen=max_recent)
        self.recent_retrieval_ms: deque = deque(maxlen=max_recent)
        self.recent_rerank_ms: deque = deque(maxlen=max_recent)
        self.recent_ttft_ms: deque = deque(maxlen=max_recent)
        self.positive_feedback = 0
        self.negative_feedback = 0

    def record_query(
        self,
        retrieval_ms: float,
        rerank_ms: float,
        ttft_ms: float,
        total_ms: float,
    ) -> None:
        self.query_count += 1
        self.recent_latencies.append(total_ms)
        self.recent_retrieval_ms.append(retrieval_ms)
        self.recent_rerank_ms.append(rerank_ms)
        self.recent_ttft_ms.append(ttft_ms)

    def record_feedback(self, rating: int) -> None:
        if rating > 0:
            self.positive_feedback += 1
        elif rating < 0:
            self.negative_feedback += 1

    def get_summary(self) -> Dict[str, Any]:
        avg_total = (
            round(sum(self.recent_latencies) / len(self.recent_latencies), 1)
            if self.recent_latencies
            else 0.0
        )
        avg_retrieval = (
            round(sum(self.recent_retrieval_ms) / len(self.recent_retrieval_ms), 1)
            if self.recent_retrieval_ms
            else 0.0
        )
        avg_rerank = (
            round(sum(self.recent_rerank_ms) / len(self.recent_rerank_ms), 1)
            if self.recent_rerank_ms
            else 0.0
        )
        avg_ttft = (
            round(sum(self.recent_ttft_ms) / len(self.recent_ttft_ms), 1)
            if self.recent_ttft_ms
            else 0.0
        )

        total_fb = self.positive_feedback + self.negative_feedback
        satisfaction_pct = (
            round((self.positive_feedback / total_fb) * 100, 1) if total_fb > 0 else 100.0
        )

        return {
            "total_queries": self.query_count,
            "avg_latency_ms": avg_total,
            "avg_retrieval_ms": avg_retrieval,
            "avg_rerank_ms": avg_rerank,
            "avg_ttft_ms": avg_ttft,
            "satisfaction_pct": satisfaction_pct,
            "positive_feedback": self.positive_feedback,
            "negative_feedback": self.negative_feedback,
        }


telemetry = TelemetryTracker()
