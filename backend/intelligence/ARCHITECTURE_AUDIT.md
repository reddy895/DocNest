# DocNest AI Intelligence Engine 2.0 — Architecture Audit

## 1. Protected Existing System Boundaries
All existing modules in `backend/app/` and `frontend/` are protected and remain unmodified:
- **Core Config (`backend/app/core/config.py`)**: Uses `DOCNEST_` env prefix, `nomic-embed-text` embeddings, `cross-encoder/ms-marco-MiniLM-L-6-v2` reranker, `llama3.2` via Ollama (`http://localhost:11434`), `chunk_size=512`, `chunk_overlap=64`, `min_relevance_score=0.30`.
- **Vector & Sparse Stores**: ChromaDB (`backend/chroma_db`, collection `docnest_collection`) and BM25Okapi (`backend/bm25_index/bm25_store.pkl`). Never deleted, recreated, or re-embedded automatically.
- **Database**: SQLite (`backend/docnest.db`) with optional MongoDB layer (`backend/app/core/mongo.py`). Schemas and existing conversations remain untouched.
- **API & SSE Contracts**: `/api/chat/stream`, `/api/documents/*`, `/api/workspaces/*`, `/api/models/*`, `/api/health`, `/api/research/*` retain exact request/response schemas.

## 2. Additive Isolation Strategy
The Intelligence Engine 2.0 lives strictly under `backend/intelligence/`:
- `feature_flags/` — independent boolean toggles (all `false` by default)
- `adapters/` — read-only wrappers around `HybridRetriever`, `CrossEncoderReranker`, and `OllamaService`
- `query_intelligence/` — intent classification, context-aware rewriting, query expansion & decomposition
- `hybrid_retrieval/` — weighted RRF fusion, metadata filters, deduplication, score normalization
- `reranking/` — lightweight lexical + cross-encoder reranking with diversity filtering & fallback
- `context_optimizer/` — token budget manager, section grouping, deduplication, style prompt templates
- `model_compatibility/` — unified LLM provider registry (Ollama, OpenAI-compatible) + embedding safety guard
- `citation_verification/` — strict source/page/chunk verification & claim-to-passage alignment
- `answer_verification/` — faithfulness check, contradiction detection, bounded retry policy
- `evaluation/` — 100+ benchmark dataset, Recall@K/MRR/NDCG/Faithfulness metrics, baseline vs enhanced runner
