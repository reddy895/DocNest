"""110-question multi-category RAG benchmark dataset across 10 question categories."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from backend.intelligence.contracts import RetrievedPassage


class BenchmarkCase(BaseModel):
    case_id: str
    category: str
    question: str
    expected_answer: str
    relevant_chunk_ids: List[str] = Field(default_factory=list)
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    doc_ids: Optional[List[str]] = None
    is_unanswerable: bool = False


CORPUS_PASSAGES: List[RetrievedPassage] = [
    RetrievedPassage(
        chunk_id="fin_p1_c0",
        doc_id="doc_fin",
        filename="Quarterly_Financial_Report.pdf",
        page_number=1,
        chunk_index=0,
        section_heading="Executive Summary",
        text="Q3 total revenue reached $48.2 million, representing a 19.4% year-over-year increase driven by enterprise subscriptions.",
        dense_score=0.72,
        sparse_score=0.65,
        rrf_score=0.032,
    ),
    RetrievedPassage(
        chunk_id="fin_p2_c1",
        doc_id="doc_fin",
        filename="Quarterly_Financial_Report.pdf",
        page_number=2,
        chunk_index=1,
        section_heading="Operating Margin Table",
        text="| Segment | Revenue ($M) | Operating Margin |\n| Cloud AI | 31.0 | 28.5% |\n| On-Prem | 17.2 | 22.1% |",
        dense_score=0.68,
        sparse_score=0.74,
        rrf_score=0.031,
    ),
    RetrievedPassage(
        chunk_id="ai_p1_c0",
        doc_id="doc_ai",
        filename="AI_Architecture_Whitepaper.pdf",
        page_number=1,
        chunk_index=0,
        section_heading="Hybrid Retrieval Pipeline",
        text="The RAG architecture combines ChromaDB dense embeddings (nomic-embed-text, 768 dimensions) with BM25Okapi sparse keyword search via Reciprocal Rank Fusion (k=60).",
        dense_score=0.79,
        sparse_score=0.81,
        rrf_score=0.033,
    ),
    RetrievedPassage(
        chunk_id="ai_p3_c2",
        doc_id="doc_ai",
        filename="AI_Architecture_Whitepaper.pdf",
        page_number=3,
        chunk_index=2,
        section_heading="Reranking & Latency Methodology",
        text="Cross-Encoder reranking with ms-marco-MiniLM-L-6-v2 evaluates top-20 candidates in 42ms median CPU latency and enforces a 0.30 abstention threshold.",
        dense_score=0.75,
        sparse_score=0.78,
        rrf_score=0.032,
    ),
    RetrievedPassage(
        chunk_id="comp_p1_c0",
        doc_id="doc_comp",
        filename="Compliance_Policy_Manual.pdf",
        page_number=1,
        chunk_index=0,
        section_heading="Data Retention & Access Control",
        text="All uploaded documents are stored locally with SHA-256 deduplication, path traversal sanitization, and workspace-level ownership isolation. Retention period is 365 days.",
        dense_score=0.70,
        sparse_score=0.71,
        rrf_score=0.030,
    ),
    RetrievedPassage(
        chunk_id="comp_p4_c1",
        doc_id="doc_comp",
        filename="Compliance_Policy_Manual.pdf",
        page_number=4,
        chunk_index=1,
        section_heading="Rate Limiting Policy",
        text="API endpoints enforce a configurable rate limit of 120 requests per minute per client IP and require JWT HS256 tokens with 24-hour expiration.",
        dense_score=0.66,
        sparse_score=0.69,
        rrf_score=0.029,
    ),
    RetrievedPassage(
        chunk_id="ml_p2_c0",
        doc_id="doc_ml",
        filename="Evaluation_Methodology_Study.pdf",
        page_number=2,
        chunk_index=0,
        section_heading="Experimental Design",
        text="In the evaluation study, chunk size 512 with 64-token overlap achieved 0.89 Recall@5 compared to 0.74 Recall@5 for naive 256-char fixed splitting.",
        dense_score=0.73,
        sparse_score=0.76,
        rrf_score=0.031,
    ),
]


_CATEGORY_TEMPLATES = [
    ("direct_factual", [
        ("What was Q3 total revenue?", "$48.2 million", ["fin_p1_c0"]),
        ("What drove the Q3 revenue increase?", "Enterprise subscriptions", ["fin_p1_c0"]),
        ("What embedding model is used in the AI architecture?", "nomic-embed-text", ["ai_p1_c0"]),
        ("What is the embedding dimension of nomic-embed-text?", "768 dimensions", ["ai_p1_c0"]),
        ("Which cross-encoder model is used for reranking?", "ms-marco-MiniLM-L-6-v2", ["ai_p3_c2"]),
        ("What is the document retention period in the compliance manual?", "365 days", ["comp_p1_c0"]),
        ("What hash algorithm is used for document deduplication?", "SHA-256", ["comp_p1_c0"]),
        ("What JWT algorithm is required by the compliance policy?", "HS256", ["comp_p4_c1"]),
        ("What is the JWT token expiration duration?", "24-hour expiration", ["comp_p4_c1"]),
        ("What is the API rate limit per client IP?", "120 requests per minute", ["comp_p4_c1"]),
        ("What RRF k constant is configured in the hybrid pipeline?", "k=60", ["ai_p1_c0"]),
    ]),
    ("technical", [
        ("How does the hybrid retrieval pipeline fuse dense and sparse results?", "Reciprocal Rank Fusion (k=60)", ["ai_p1_c0"]),
        ("Which vector store and sparse index are combined in the whitepaper?", "ChromaDB and BM25Okapi", ["ai_p1_c0"]),
        ("How many top candidates does the cross-encoder evaluate?", "top-20 candidates", ["ai_p3_c2"]),
        ("What abstention threshold is enforced after reranking?", "0.30", ["ai_p3_c2"]),
        ("How are uploaded files protected against path attacks?", "path traversal sanitization", ["comp_p1_c0"]),
        ("What isolation boundary is enforced for documents?", "workspace-level ownership isolation", ["comp_p1_c0"]),
        ("What chunking configuration is evaluated in the methodology study?", "chunk size 512 with 64-token overlap", ["ml_p2_c0"]),
        ("What authentication token format is enforced on API routes?", "JWT HS256", ["comp_p4_c1"]),
        ("How is duplicate file ingestion prevented?", "SHA-256 deduplication", ["comp_p1_c0"]),
        ("What is the dense embedding dimension size?", "768 dimensions", ["ai_p1_c0"]),
        ("What sparse retrieval algorithm is used alongside ChromaDB?", "BM25Okapi", ["ai_p1_c0"]),
    ]),
    ("multi_document", [
        ("Summarize the security controls and RAG latency threshold across the manuals.", "365-day retention, SHA-256, 0.30 threshold, 42ms", ["comp_p1_c0", "ai_p3_c2"]),
        ("How do the AI whitepaper and evaluation study configure retrieval and chunking?", "ChromaDB+BM25 RRF k=60 and 512/64 chunking", ["ai_p1_c0", "ml_p2_c0"]),
        ("List the revenue growth and API rate limit across the financial and compliance reports.", "$48.2M (19.4% YoY) and 120 req/min", ["fin_p1_c0", "comp_p4_c1"]),
        ("What are the Cloud AI margin and cross-encoder CPU latency across reports?", "28.5% margin and 42ms latency", ["fin_p2_c1", "ai_p3_c2"]),
        ("Combine the data retention rule and Recall@5 improvement across documents.", "365 days retention and 0.89 Recall@5", ["comp_p1_c0", "ml_p2_c0"]),
        ("Which documents describe authentication tokens and embedding dimensions?", "Compliance Manual (JWT HS256) and AI Whitepaper (768-dim)", ["comp_p4_c1", "ai_p1_c0"]),
        ("What are the On-Prem revenue and abstention threshold across the files?", "$17.2M and 0.30", ["fin_p2_c1", "ai_p3_c2"]),
        ("Summarize both subscription growth drivers and workspace isolation.", "Enterprise subscriptions and workspace-level isolation", ["fin_p1_c0", "comp_p1_c0"]),
        ("How do the compliance policy and whitepaper address security and reranking?", "Path sanitization/JWT and ms-marco-MiniLM-L-6-v2", ["comp_p1_c0", "ai_p3_c2"]),
        ("Report both Cloud AI revenue and 512-token chunk Recall@5.", "$31.0M and 0.89 Recall@5", ["fin_p2_c1", "ml_p2_c0"]),
        ("Identify the RRF constant and JWT expiration across the whitepaper and manual.", "k=60 and 24-hour expiration", ["ai_p1_c0", "comp_p4_c1"]),
    ]),
    ("research_methodology", [
        ("What experimental chunking design was tested in the evaluation study?", "512 chunk size with 64-token overlap vs 256-char", ["ml_p2_c0"]),
        ("How was reranking latency measured in the whitepaper?", "42ms median CPU latency over top-20 candidates", ["ai_p3_c2"]),
        ("What baseline was chunk size 512 compared against?", "naive 256-char fixed splitting", ["ml_p2_c0"]),
        ("How does the architecture combine lexical and semantic signals?", "BM25Okapi + ChromaDB via RRF k=60", ["ai_p1_c0"]),
        ("What guardrail prevents low-confidence hallucinations?", "0.30 abstention threshold", ["ai_p3_c2"]),
        ("Which metric was used to benchmark chunking strategies?", "Recall@5", ["ml_p2_c0"]),
        ("What candidate pool size is passed to the cross-encoder?", "top-20 candidates", ["ai_p3_c2"]),
        ("How does the system handle duplicate document uploads?", "SHA-256 deduplication", ["comp_p1_c0"]),
        ("What token overlap is paired with 512 chunk size?", "64-token overlap", ["ml_p2_c0"]),
        ("Which cross-encoder architecture evaluates passage relevance?", "ms-marco-MiniLM-L-6-v2", ["ai_p3_c2"]),
        ("How is rate limiting enforced on research APIs?", "120 requests per minute per client IP", ["comp_p4_c1"]),
    ]),
    ("numerical", [
        ("What was the year-over-year revenue growth percentage in Q3?", "19.4%", ["fin_p1_c0"]),
        ("What is the median CPU reranking latency in milliseconds?", "42ms", ["ai_p3_c2"]),
        ("What Recall@5 did 512/64 chunking achieve?", "0.89", ["ml_p2_c0"]),
        ("What Recall@5 did 256-char fixed splitting achieve?", "0.74", ["ml_p2_c0"]),
        ("How many days are documents retained?", "365 days", ["comp_p1_c0"]),
        ("How many requests per minute are allowed by rate limiting?", "120", ["comp_p4_c1"]),
        ("How many hours until JWT tokens expire?", "24-hour", ["comp_p4_c1"]),
        ("What is the RRF k parameter value?", "60", ["ai_p1_c0"]),
        ("What is the abstention relevance threshold?", "0.30", ["ai_p3_c2"]),
        ("How many dimensions does nomic-embed-text produce?", "768", ["ai_p1_c0"]),
        ("What was Q3 total revenue in millions?", "$48.2 million", ["fin_p1_c0"]),
    ]),
    ("table_based", [
        ("What is the Cloud AI segment revenue in the operating margin table?", "$31.0M", ["fin_p2_c1"]),
        ("What is the Cloud AI operating margin?", "28.5%", ["fin_p2_c1"]),
        ("What is the On-Prem segment revenue in the table?", "$17.2M", ["fin_p2_c1"]),
        ("What is the On-Prem operating margin?", "22.1%", ["fin_p2_c1"]),
        ("Which segment has the higher operating margin in the table?", "Cloud AI (28.5% vs 22.1%)", ["fin_p2_c1"]),
        ("Which segment generated more revenue in the operating margin table?", "Cloud AI ($31.0M)", ["fin_p2_c1"]),
        ("What is the difference in operating margin between Cloud AI and On-Prem?", "6.4 percentage points", ["fin_p2_c1"]),
        ("List both segments shown in the operating margin table.", "Cloud AI and On-Prem", ["fin_p2_c1"]),
        ("What unit is used for segment revenue in the table?", "$M (millions)", ["fin_p2_c1"]),
        ("Does On-Prem exceed 25% operating margin?", "No, it is 22.1%", ["fin_p2_c1"]),
        ("What is the combined revenue of Cloud AI and On-Prem in the table?", "$48.2M", ["fin_p2_c1", "fin_p1_c0"]),
    ]),
    ("follow_up", [
        ("What is its median CPU latency?", "42ms", ["ai_p3_c2"]),
        ("What about its embedding dimensions?", "768 dimensions", ["ai_p1_c0"]),
        ("How much did it grow year-over-year?", "19.4%", ["fin_p1_c0"]),
        ("What is their operating margin?", "28.5% for Cloud AI and 22.1% for On-Prem", ["fin_p2_c1"]),
        ("How long are they retained?", "365 days", ["comp_p1_c0"]),
        ("What overlap does it use?", "64-token overlap", ["ml_p2_c0"]),
        ("When do those tokens expire?", "24-hour expiration", ["comp_p4_c1"]),
        ("What threshold does it enforce?", "0.30", ["ai_p3_c2"]),
        ("What drove that increase?", "Enterprise subscriptions", ["fin_p1_c0"]),
        ("What was it compared against?", "256-char fixed splitting", ["ml_p2_c0"]),
        ("What algorithm does it use for tokens?", "JWT HS256", ["comp_p4_c1"]),
    ]),
    ("comparison", [
        ("Compare Cloud AI and On-Prem operating margins.", "Cloud AI 28.5% vs On-Prem 22.1%", ["fin_p2_c1"]),
        ("Compare 512/64 chunking vs 256-char fixed splitting Recall@5.", "0.89 vs 0.74 Recall@5", ["ml_p2_c0"]),
        ("Compare Cloud AI revenue and On-Prem revenue.", "$31.0M vs $17.2M", ["fin_p2_c1"]),
        ("Contrast dense ChromaDB retrieval and BM25Okapi retrieval in the pipeline.", "Dense semantic embeddings vs sparse keyword search fused via RRF", ["ai_p1_c0"]),
        ("Compare the chunk size and overlap in the methodology study.", "512 chunk size vs 64-token overlap", ["ml_p2_c0"]),
        ("Compare the retention policy and JWT expiration timelines.", "365 days retention vs 24-hour JWT expiration", ["comp_p1_c0", "comp_p4_c1"]),
        ("Compare Q3 total revenue against Cloud AI segment revenue.", "$48.2M total vs $31.0M Cloud AI", ["fin_p1_c0", "fin_p2_c1"]),
        ("Contrast the reranker candidate pool size with the abstention threshold.", "top-20 candidates vs 0.30 threshold", ["ai_p3_c2"]),
        ("Compare workspace isolation with rate limiting in the compliance manual.", "Ownership isolation per workspace vs 120 req/min IP limit", ["comp_p1_c0", "comp_p4_c1"]),
        ("Compare semantic vector search and cross-encoder reranking stages.", "Bi-encoder ChromaDB retrieval vs Cross-Encoder MiniLM scoring", ["ai_p1_c0", "ai_p3_c2"]),
        ("Contrast the Recall@5 improvement between chunkers.", "+0.15 Recall@5 improvement", ["ml_p2_c0"]),
    ]),
    ("missing_information", [
        ("What was the Q4 revenue forecast?", "Insufficient evidence", []),
        ("Who is the Chief Financial Officer of the company?", "Insufficient evidence", []),
        ("What GPU model was used to train nomic-embed-text?", "Insufficient evidence", []),
        ("What is the customer churn rate in Europe?", "Insufficient evidence", []),
        ("Which cloud vendor hosts the production Kubernetes cluster?", "Insufficient evidence", []),
        ("What was the Q1 operating margin for Hardware?", "Insufficient evidence", []),
        ("How many employees work in the AI research division?", "Insufficient evidence", []),
        ("What is the exact price of an enterprise license?", "Insufficient evidence", []),
        ("Which GDPR article number is cited in Appendix B?", "Insufficient evidence", []),
        ("What BLEU score did Llama 3.2 achieve on French translation?", "Insufficient evidence", []),
        ("What is the office street address in the compliance manual?", "Insufficient evidence", []),
    ]),
    ("unanswerable", [
        ("What will the stock price be next Tuesday?", "Unanswerable", []),
        ("Who won the 1998 World Cup final?", "Unanswerable", []),
        ("What is the secret admin password for the database?", "Unanswerable", []),
        ("How many planets orbit Proxima Centauri?", "Unanswerable", []),
        ("What is the weather forecast for Tokyo tomorrow?", "Unanswerable", []),
        ("Can you guess the CEO's personal phone number?", "Unanswerable", []),
        ("What is the capital city of Mars?", "Unanswerable", []),
        ("Which lottery numbers will win this Friday?", "Unanswerable", []),
        ("What color shirt is the author wearing?", "Unanswerable", []),
        ("How many jellybeans are in the jar on floor 3?", "Unanswerable", []),
        ("Predict Q4 net profit without any Q4 data.", "Unanswerable", []),
    ]),
]


def build_benchmark_dataset() -> List[BenchmarkCase]:
    """Build all 110 verified benchmark questions across 10 categories."""
    cases: List[BenchmarkCase] = []
    idx = 1
    follow_up_contexts = [
        "Cross-Encoder reranking with ms-marco-MiniLM-L-6-v2",
        "nomic-embed-text embeddings",
        "Q3 total revenue",
        "Cloud AI and On-Prem operating margins",
        "uploaded compliance documents",
        "chunk size 512 evaluation",
        "JWT HS256 tokens",
        "reranking abstention guardrail",
        "Q3 revenue increase",
        "chunk size 512 Recall@5",
        "compliance authentication",
    ]
    for category, items in _CATEGORY_TEMPLATES:
        for item_idx, (q, ans, rel_ids) in enumerate(items):
            history = []
            if category == "follow_up":
                history = [{"sender": "user", "text": follow_up_contexts[item_idx]}]
            cases.append(
                BenchmarkCase(
                    case_id=f"bench_{idx:03d}",
                    category=category,
                    question=q,
                    expected_answer=ans,
                    relevant_chunk_ids=rel_ids,
                    chat_history=history,
                    is_unanswerable=(category in {"missing_information", "unanswerable"}),
                )
            )
            idx += 1
    return cases
