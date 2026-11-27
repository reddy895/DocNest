# DocNest AI Intelligence Engine 2.0

An isolated, additive enhancement layer built around DocNest's existing RAG pipeline. Every module is gated behind independent feature flags (all `false` by default) and degrades gracefully to the existing baseline on error.

## Feature Flags

Configure via environment variables (with or without `DOCNEST_` prefix):

```env
ENABLE_QUERY_INTELLIGENCE=false
ENABLE_HYBRID_SEARCH=false
ENABLE_RERANKING=false
ENABLE_CONTEXT_OPTIMIZATION=false
ENABLE_MODEL_COMPATIBILITY=false
ENABLE_CITATION_VERIFICATION=false
ENABLE_ANSWER_VERIFICATION=false
ENABLE_EVIDENCE_GROUNDING=false
ENABLE_PROJECT_INTELLIGENCE=false
ENABLE_CLAIM_VERIFICATION=false
```

## Modules

- `feature_flags/manager.py`: Independent env-backed flag reader with per-instance overrides.
- `adapters/`: Read-only wrappers (`ExistingRetrieverAdapter`, `ExistingRerankerAdapter`, `ExistingOllamaAdapter`) and circuit-breaker fallback helpers.
- `query_intelligence/`: Intent classification, conversation context rewriting, conservative domain expansion, and multi-doc decomposition.
- `hybrid_retrieval/`: Min-max normalization, metadata filters (doc, page, workspace, section), weighted RRF fusion, deduplication, and embedding-dimension safety guard.
- `reranking/`: Lightweight lexical overlap scorer, safe Cross-Encoder adapter, and MMR diversity filter.
- `context_optimizer/`: Token budget manager, section-aware reading-order organizer, and 5 answer style prompt templates (`concise`, `detailed`, `technical`, `research`, `beginner`).
- `model_compatibility/`: Unified `LLMProvider` interface for Ollama & OpenAI-compatible endpoints, capability registry (`Llama`, `Qwen`, `Gemma`, `Mistral`), and embedding-collection mismatch protection.
- `citation_verification/` & `answer_verification/`: Inline `[Filename, p. X]` validation, claim-to-passage alignment, faithfulness checking, and bounded retry policy (`max_retries=1`).
- `evaluation/`: 110-question benchmark across 10 categories with Recall@5, Precision@5, MRR, NDCG@5, and latency reporting.

## Measured Benchmark Results (110 Questions)

| Profile | Recall@5 | Precision@5 | MRR | NDCG@5 | Mean Latency (ms) |
|---|---:|---:|---:|---:|---:|
| `baseline` | 0.8000 | 0.3845 | 0.7712 | 0.7728 | 0.13 |
| `query_intelligence` | 0.8000 | 0.3659 | 0.7712 | 0.7728 | 0.13 |
| `hybrid_retrieval` | 0.8000 | 0.3845 | 0.6074 | 0.6499 | 0.20 |
| `reranking` | 0.7455 | 0.6818 | 0.7636 | 0.7371 | 0.16 |
| `context_optimization` | 0.8000 | 0.3845 | 0.6841 | 0.7123 | 0.16 |
| `combined_enhancements` | 0.7455 | 0.6864 | 0.7500 | 0.7287 | 0.30 |

## Commands

```bash
# Run Intelligence Engine 2.0 unit & integration tests
PYTHONPATH=. .venv/bin/pytest backend/intelligence/tests/

# Run existing regression test suite
.venv/bin/pytest tests/

# Run 110-question retrieval benchmark comparison
.venv/bin/python -m backend.intelligence.evaluation.runner

# Run 100-question hallucination & deep project benchmark
.venv/bin/python -m backend.intelligence.evaluation.hallucination_benchmark

# Run complete backend + intelligence test suite (77 tests)
PYTHONPATH=. .venv/bin/pytest backend/intelligence/tests/ tests/
```

