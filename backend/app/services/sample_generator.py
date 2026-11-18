import logging
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.app.core.config import settings

logger = logging.getLogger("docnest.samples")


def generate_sample_pdfs() -> None:
    """Generate three enterprise-grade curated sample PDFs for instant onboarding."""
    samples_dir = settings.SAMPLES_DIR
    samples_dir.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()

    # Title style
    title_style = ParagraphStyle(
        'DocNestTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#202326"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        'DocNestH2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#303538"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'DocNestBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#202326"),
        spaceAfter=6,
    )

    # 1. Quarterly Financial Report Q3
    fin_path = samples_dir / "quarterly_financial_report.pdf"
    if not fin_path.exists():
        doc = SimpleDocTemplate(str(fin_path), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        story = [
            Paragraph("DocNest Global Technologies — Q3 Financial Performance Report", title_style),
            Paragraph("Fiscal Period Ending September 30, 2026 | Prepared by Corporate Finance", body_style),
            Spacer(1, 12),
            Paragraph("1. Executive Financial Summary", heading_style),
            Paragraph("During the third fiscal quarter of 2026, DocNest achieved total consolidated revenue of $142.8 million, representing an increase of 28.4% year-over-year. Operating income rose to $38.2 million, resulting in an operating margin of 26.7%, driven by enterprise RAG cloud subscription expansion and local appliance deployment synergies.", body_style),
            Spacer(1, 8),
            Paragraph("2. Segment Revenue & Performance Matrix", heading_style),
            Table(
                [
                    ["Business Segment", "Q3 2026 Revenue", "Q3 2025 Revenue", "YoY Growth", "Gross Margin"],
                    ["Enterprise Subscriptions", "$86.4M", "$62.1M", "+39.1%", "78.4%"],
                    ["Professional Services", "$24.2M", "$22.5M", "+7.5%", "42.0%"],
                    ["Hardware Appliances", "$32.2M", "$26.6M", "+21.0%", "54.2%"],
                    ["Consolidated Total", "$142.8M", "$111.2M", "+28.4%", "66.8%"],
                ],
                colWidths=[150, 90, 90, 75, 80],
                style=TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#303538")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#F4D21F")),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BFC3C7")),
                ])
            ),
            Spacer(1, 14),
            Paragraph("3. Operational Risk Factors and Outlook", heading_style),
            Paragraph("Key risks for the upcoming fiscal quarter include semiconductor supply lead times for on-premise inference servers, localized currency exchange fluctuations across EMEA markets, and regulatory compliance requirements regarding local data residency laws. Cash reserves remain resilient at $215.4 million with zero long-term debt.", body_style),
        ]
        doc.build(story)
        logger.info(f"Generated sample financial report at {fin_path}")

    # 2. AI Architecture Whitepaper
    ai_path = samples_dir / "ai_architecture_whitepaper.pdf"
    if not ai_path.exists():
        doc = SimpleDocTemplate(str(ai_path), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        story = [
            Paragraph("Enterprise RAG System Architecture & LLM Orchestration", title_style),
            Paragraph("Technical Whitepaper v2.4 | Architecture Systems Group", body_style),
            Spacer(1, 12),
            Paragraph("1. High-Density Retrieval and Ingestion Pipeline", heading_style),
            Paragraph("The DocNest core engine utilizes a dual-path hybrid retrieval pipeline designed for sub-100 millisecond response times on resource-constrained enterprise nodes (12GB to 16GB RAM). Layout-aware ingestion transforms unstructured PDFs into section-attributed Markdown representations, preserving table borders and multi-column heading hierarchies.", body_style),
            Spacer(1, 8),
            Paragraph("2. Dense Vector and BM25 Sparse Index Fusion", heading_style),
            Paragraph("Vector embeddings are generated using Ollama's local nomic-embed-text model (768-dimensional space), indexed inside ChromaDB with HNSW cosine similarity. Concurrently, an inverted BM25 index scores token frequencies. Top-K candidate passages from dense and sparse retrieval channels are fused via Reciprocal Rank Fusion (RRF):", body_style),
            Paragraph("<b>RRF Score Formula:</b> RRF(d) = SUM( 1 / (60 + rank_dense(d)) + 1 / (60 + rank_sparse(d)) )", body_style),
            Spacer(1, 8),
            Paragraph("3. Cross-Encoder Reranking and Abstention Guardrails", heading_style),
            Paragraph("Candidate passages are evaluated by cross-encoder/ms-marco-MiniLM-L-6-v2. If all retrieved candidates fall below the minimum relevance confidence threshold (default 0.30), the generation phase halts immediately with an explicit abstention notice to prevent hallucination.", body_style),
        ]
        doc.build(story)
        logger.info(f"Generated sample AI whitepaper at {ai_path}")

    # 3. Compliance Policy Manual
    comp_path = samples_dir / "compliance_policy_manual.pdf"
    if not comp_path.exists():
        doc = SimpleDocTemplate(str(comp_path), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        story = [
            Paragraph("Corporate Information Security & Compliance Policy Manual", title_style),
            Paragraph("Policy Document SEC-2026-B | Office of Information Governance", body_style),
            Spacer(1, 12),
            Paragraph("1. Access Control and Multi-Factor Authentication", heading_style),
            Paragraph("All personnel accessing internal documents, client telemetry, or production infrastructure must authenticate via corporate identity providers enforcing hardware token-based Multi-Factor Authentication (MFA). Session tokens expire after a maximum inactivity period of 60 minutes, requiring explicit re-authentication.", body_style),
            Spacer(1, 8),
            Paragraph("2. Data Classification and Encryption Standards", heading_style),
            Paragraph("Data stored within DocNest repositories is classified into three levels: Public, Internal Confidential, and Restricted PII. All data in transit must enforce TLS 1.3 encryption. At-rest persistent storage across SQLite databases, ChromaDB vector stores, and local disk volumes must be encrypted with AES-256.", body_style),
            Spacer(1, 8),
            Paragraph("3. Incident Response and Breach Notification Timelines", heading_style),
            Paragraph("In the event of a suspected data security breach or unauthorized access incident, the Incident Response Team (IRT) must be alerted within 15 minutes of anomaly confirmation. Affected business units and relevant regulatory bodies must be notified in writing within 72 hours under GDPR Article 33 guidelines.", body_style),
        ]
        doc.build(story)
        logger.info(f"Generated sample compliance policy manual at {comp_path}")
