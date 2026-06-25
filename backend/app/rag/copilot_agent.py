import time
import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.chat import ChatSession, ChatMessage
from app.models.research_report import ResearchReport
from app.models.watchlist import Watchlist
from app.rag.retriever import retrieve
from app.rag.llm_service import ask_llm

from app.services.financial_data import normalize_company_name, COMPANIES_MAP

logger = logging.getLogger(__name__)

def detect_company(text: str) -> str:
    text_lower = text.lower()
    sorted_keys = sorted(COMPANIES_MAP.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in text_lower:
            return COMPANIES_MAP[key]
    return None


def detect_sector(text: str) -> str:
    text_lower = text.lower()
    sectors = ["banking", "telecom", "metals", "real estate", "tech", "crypto", "automotive", "finance"]
    for s in sectors:
        if s in text_lower:
            return s.capitalize()
    return None


def get_default_followups(company: str = None, sector: str = None) -> list:
    if company:
        return [
            f"Compare {company} with its main peers",
            f"What are the key valuation metrics for {company}?",
            f"Show the biggest threat vectors for {company}",
            f"Analyze recent earnings outlook for {company}"
        ]
    elif sector:
        return [
            f"Which stocks are leading in the {sector} sector?",
            f"What are the regulatory risks in {sector}?",
            f"How does high interest rate affect {sector}?"
        ]
    return [
        "What are today's major market catalysts?",
        "Compare private bank valuations",
        "Summarize recent RBI policy decisions"
    ]


def answer_copilot_question(
    db: Session,
    session_id: str,
    question: str,
    user_id: uuid.UUID,
    deep_research: bool = False
) -> dict:
    if isinstance(session_id, str):
        try:
            session_id = uuid.UUID(session_id)
        except ValueError:
            pass

    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        session = ChatSession(id=session_id, user_id=user_id, title=question[:40] + "...")
        db.add(session)
        db.commit()
        db.refresh(session)

    # 1. Rolling Context & Message Memory Window (Last 20 messages)
    history_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    history_messages.reverse()

    total_messages_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
    if total_messages_count > 20 and not session.summary:
        summary_prompt = "Summarize the key topics and decisions from the following chat conversation history:\n"
        for msg in history_messages[:-5]:
            summary_prompt += f"{msg.role.upper()}: {msg.content}\n"
        try:
            session.summary = ask_llm(summary_prompt, article_title="History Summary")
            db.commit()
        except Exception:
            pass

    # 2. Company Research Mode & Caching Check
    company = detect_company(question)
    sector = detect_sector(question)

    cached_research = None
    if company:
        yesterday = datetime.utcnow() - timedelta(hours=24)
        cached = (
            db.query(ResearchReport)
            .filter(ResearchReport.entity_name == company, ResearchReport.created_at >= yesterday)
            .order_by(ResearchReport.created_at.desc())
            .first()
        )
        if cached:
            cached_research = cached.report_data.get("report_text")

    # Start timing for RAG metrics logging
    rag_start = time.time()

    # 3. Knowledge Integration via Hybrid Retrieval (pass user_id for complete data isolation!)
    search_queries = [question]
    if deep_research:
        search_queries.append(f"{company or sector or 'market'} latest earnings and management commentary")
        search_queries.append(f"{company or sector or 'market'} key risks and catalysts")

    retrieved_docs = []
    seen_titles = set()
    for sq in search_queries:
        docs = retrieve(sq, user_id=user_id, include_research_library=deep_research)
        for d in docs:
            if d["title"] not in seen_titles:
                seen_titles.add(d["title"])
                retrieved_docs.append(d)

    context_str = "\n".join([
        f"- TITLE: {d['title']}\n  SOURCE: {d.get('source', 'General')}\n  URL: {d.get('url', '')}\n  TEXT: {d.get('text', '')[:2000]}"
        for d in retrieved_docs[:8]
    ])

    # 4. Prompt Templating based on topic type
    template_type = "General Inquiry"
    if company:
        template_type = "Company Research Dossier"
        template_instruction = f"""
You are an elite financial research copilot (similar to Bloomberg GPT). Analyze {company} and compile a dossier.
Format your response using this structure:

# COMPANY OVERVIEW: {company}

## Business Model
...
## Revenue Segments
...
## Competitive Position
...
## Financial Highlights
...
## Recent News
...
## Management Commentary
...
## Key Risks
...
## Growth Opportunities
...
## Valuation Insights
...
## Investment Thesis
...
## Bull Case
...
## Bear Case
...
## Conclusion
"""
    elif sector:
        template_type = "Sector Analysis"
        template_instruction = f"""
You are an expert sector analyst. Analyze the {sector} sector.
Format your response using this structure:

# SECTOR ANALYSIS: {sector}

## Sector Momentum & Trends
...
## Top Sector Catalysts
...
## Key Risks
...
## Peer Comparisons & Valuations
...
## Sector Sentiment & Outlook
...
"""
    else:
        template_instruction = """
You are a global macro economist and financial analyst. Answer the user prompt.
Provide structured layout:
- Economic Context
- Market Dynamics
- Equity & Debt Implications
- Outlook
"""

    prompt = f"""You are a professional financial copilot named "MarketBeacon Copilot".

{template_instruction}

Conversation Summary Context:
{session.summary or "No previous summary."}

Recent Message Context (Multi-turn chat memory):
"""
    for msg in history_messages:
        prompt += f"{msg.role.upper()}: {msg.content}\n"

    prompt += f"""
CURRENT USER QUESTION: {question}

INTEGRATED KNOWLEDGE SOURCE CONTEXT (RAG):
{context_str or "No matching documentation retrieved."}

INSTRUCTIONS FOR CITATION-AWARE RESPONSES:
Generate your final answer using exactly these headings in Markdown:

# Summary
Provide a high-level executive summary of the response.

# Evidence
Provide detailed evidence, statistics, and findings. 
CITATION RULE: Every major statement, statistic, or earnings number must explicitly include its source in-line (e.g., "[Source: economic_times_markets]" or "[Source: TCS Q4 FY26 Investor Presentation]").

# Sources
Summarize the list of source references used.

# Confidence Score
Provide an AI research confidence score between 0% and 100% based on the retrieved details and reliability of evidence. Format it exactly as:
[AI-Generated Research Confidence Score: XX%]

# Suggested Follow-Ups
Provide 3 suggested follow-up questions for further research.
"""

    # Calculate overall evidence score
    from app.services.reliability_layer import get_source_tier_info
    for d in retrieved_docs:
        doc_type = d.get("document_type", "")
        src_label = d.get("source", "")
        tier_info = get_source_tier_info(doc_type, src_label)
        d["source_weight"] = tier_info["weight"]
        d["source_tier"] = tier_info["tier"]
        d["source_tier_label"] = tier_info["label"]
        d["source_description"] = tier_info["description"]
        
    retrieved_docs = sorted(
        retrieved_docs,
        key=lambda x: x.get("adjusted_score", 0.0) if "adjusted_score" in x else x.get("similarity_score", 0.5) * x.get("source_weight", 0.5),
        reverse=True
    )

    top_docs = retrieved_docs[:5]
    evidence_score = 0.0
    if top_docs:
        for d in top_docs:
            sim = d.get("similarity_score", 0.6)
            weight = d.get("source_weight", 0.6)
            evidence_score += sim * weight

    is_weak_evidence = (evidence_score < 1.0)
    
    response_text = ""
    confidence_score_int = 10
    research_quality_badge = "Limited Evidence"
    citation_coverage = 0.0

    if is_weak_evidence:
        response_text = "Insufficient evidence available."
        confidence_score_int = 10
        research_quality_badge = "Limited Evidence"
    elif company and cached_research:
        response_text = f"[CACHED RESEARCH DOSSIER FOR {company.upper()} - LAST 24 HOURS]\n\n" + cached_research
        citation_coverage = 0.8
        confidence_score_int = 85
        research_quality_badge = "High Confidence"
    else:
        try:
            response_text = ask_llm(prompt, article_title=f"Copilot Chat: {session.title}")
            if company:
                report = ResearchReport(
                    entity_name=company,
                    report_data={"report_text": response_text},
                    created_at=datetime.utcnow()
                )
                db.add(report)
                db.commit()
        except Exception as e:
            response_text = f"An error occurred generating response: {str(e)}"

    if "insufficient evidence" in response_text.lower():
        confidence_score_int = 10
        research_quality_badge = "Limited Evidence"
        citation_coverage = 0.0
    elif not is_weak_evidence and not (company and cached_research):
        cited_count = 0
        text_lower = response_text.lower()
        for d in top_docs:
            title = d.get("title", "").lower()
            source_file = d.get("source_file", "").lower()
            source_name = d.get("source", "").lower()
            
            if (title and title in text_lower) or \
               (source_file and source_file in text_lower) or \
               (source_name and source_name in text_lower):
                cited_count += 1
        
        citation_coverage = float(cited_count / len(top_docs)) if top_docs else 0.0
        
        avg_sim = sum(d.get("similarity_score", 0.6) for d in top_docs) / len(top_docs) if top_docs else 0.0
        avg_weight = sum(d.get("source_weight", 0.6) for d in top_docs) / len(top_docs) if top_docs else 0.0
        
        conf_pct = (avg_sim * 0.4 + avg_weight * 0.4 + citation_coverage * 0.2)
        confidence_score_int = max(10, min(100, int(conf_pct * 100)))
        
        if confidence_score_int >= 75:
            research_quality_badge = "High Confidence"
        elif confidence_score_int >= 40:
            research_quality_badge = "Medium Confidence"
        else:
            research_quality_badge = "Limited Evidence"

    # End timing for metrics logging
    latency_ms = (time.time() - rag_start) * 1000
    token_estimate = (len(prompt) // 4) + (len(response_text) // 4)

    # Log metrics to Postgres research_metrics table with user_id
    try:
        from app.models.research_metric import ResearchMetric
        metric = ResearchMetric(
            user_id=user_id,
            session_id=str(session.id),
            query=question,
            retrieved_count=len(retrieved_docs),
            reranked_count=len(retrieved_docs),
            sources_used=[
                {
                    "document_id": d.get("document_id"),
                    "source_file": d.get("source_file"),
                    "company_name": d.get("company_name"),
                    "document_type": d.get("document_type"),
                    "chunk_index": d.get("chunk_index"),
                    "similarity_score": d.get("similarity_score", 0.6),
                    "source_weight": d.get("source_weight", 0.6),
                    "source_tier": d.get("source_tier", 3),
                    "text": d.get("text", "")[:200]
                }
                for d in retrieved_docs[:5]
            ],
            latency_ms=latency_ms,
            token_estimate=token_estimate,
            retrieval_quality=float(sum(d.get("similarity_score", 0.6) for d in top_docs)/len(top_docs)) if top_docs else 0.0,
            confidence_score=float(confidence_score_int),
            citation_coverage=float(citation_coverage)
        )
        db.add(metric)
        db.commit()
        logger.info(f"[Metrics Log] Logged query stats to research_metrics: Latency={latency_ms:.2f}ms, Chunks={len(retrieved_docs)} (User: {user_id})")
    except Exception as em:
        db.rollback()
        logger.exception(f"[Metrics Log] Failed to save research metric record: {em}")

    # Save messages to database
    try:
        user_msg = ChatMessage(session_id=session.id, role="user", content=question)
        assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=response_text)
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()
    except Exception as ec:
        db.rollback()
        logger.exception(f"[Chat History Log] Failed to save chat messages: {ec}")

    sources = [
        {
            "title": d["title"],
            "url": d.get("url", ""),
            "source": d.get("source", "General"),
            "document_id": d.get("document_id"),
            "source_file": d.get("source_file"),
            "company_name": d.get("company_name"),
            "document_type": d.get("document_type"),
            "chunk_index": d.get("chunk_index"),
            "similarity_score": d.get("similarity_score", 0.6),
            "source_weight": d.get("source_weight", 0.6),
            "source_tier": d.get("source_tier", 3),
            "source_tier_label": d.get("source_tier_label", "Tier 3"),
            "text": d.get("text", "")
        }
        for d in retrieved_docs[:8]
    ]

    return {
        "session_id": str(session.id),
        "answer": response_text,
        "sources": sources,
        "detected_company": company,
        "template_type": template_type,
        "suggested_followups": get_default_followups(company, sector),
        "confidence_score": confidence_score_int,
        "research_quality_badge": research_quality_badge,
        "evidence_score": float(round(evidence_score, 2)),
        "citation_coverage": float(round(citation_coverage, 2))
    }
