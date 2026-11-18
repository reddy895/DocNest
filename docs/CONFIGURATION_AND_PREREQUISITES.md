# DocNest Platform — Configuration & Local Model Prerequisites

## 1. Local Hardware & Runtime Requirements

DocNest is engineered for local deployment on developer workstations with **12 GB RAM**:

| Component | Target Model | Quantization / Footprint | Purpose |
| :--- | :--- | :--- | :--- |
| **LLM Inference** | `llama3.2:3b` | 2.0 GB VRAM / System RAM | Factual question answering, query rewriting |
| **Embeddings** | `nomic-embed-text` | 274 MB | Dense vector representations (8192 context window) |
| **Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | ~80 MB | Query-passage relevance cross-attention |
| **Sparse Index** | BM25 (`rank_bm25`) | In-memory (~5 MB) | Exact keyword matching |

---

## 2. Ollama Local Setup

Ensure [Ollama](https://ollama.com/) is installed and running on `http://localhost:11434`:

```bash
# 1. Pull the generation model
ollama pull llama3.2

# 2. Pull the dense embedding model
ollama pull nomic-embed-text

# 3. Verify models are active
ollama list
```

---

## 3. Environment Variable Reference

All configuration options support overrides through `.env` using the `DOCNEST_` prefix:

| Environment Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DOCNEST_ENV` | `production` | Deployment mode (`development`, `test`, `production`) |
| `DOCNEST_API_HOST` | `0.0.0.0` | Bind host address |
| `DOCNEST_API_PORT` | `8000` | Bind port number |
| `DOCNEST_CORS_ORIGINS` | `["http://localhost:5173", ...]` | Allowed CORS origins for web clients |
| `DOCNEST_JWT_SECRET_KEY` | *(Set securely in prod)* | HMAC secret key used to sign JWT auth tokens |
| `DOCNEST_JWT_ALGORITHM` | `HS256` | JWT cryptographic algorithm |
| `DOCNEST_JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Access token lifespan in minutes (24h) |
| `DOCNEST_DB_PATH` | `backend/docnest.db` | Path to persistent SQLite database |
| `DOCNEST_DOCUMENTS_DIR` | `backend/documents` | Storage folder for uploaded PDF binaries |
| `DOCNEST_CHROMA_DIR` | `backend/chroma_db` | Persistent ChromaDB vector directory |
| `DOCNEST_BM25_DIR` | `backend/bm25_index` | Persistent BM25 inverted index storage |
| `DOCNEST_EMBEDDING_MODEL` | `nomic-embed-text` | Ollama dense embedding model identifier |
| `DOCNEST_RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Hugging Face cross-encoder reranker |
| `DOCNEST_CHUNK_SIZE` | `512` | Target chunk size in tokens/characters |
| `DOCNEST_CHUNK_OVERLAP` | `64` | Overlap between adjacent chunks |
| `DOCNEST_RETRIEVAL_TOP_K`| `5` | Final candidates forwarded to LLM generation |
| `DOCNEST_MIN_RELEVANCE_SCORE`| `0.30` | Abstention threshold for reranker relevance |
| `DOCNEST_HYBRID_SEARCH_ENABLED`| `true` | Combine dense ChromaDB with sparse BM25 |
| `DOCNEST_RERANKER_ENABLED`| `true` | Apply cross-encoder reranking after RRF fusion |
| `DOCNEST_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama HTTP endpoint |
| `DOCNEST_OLLAMA_MODEL` | `llama3.2` | Active Ollama model name |
| `DOCNEST_MAX_FILE_SIZE_MB`| `50` | Maximum upload file limit in megabytes |
