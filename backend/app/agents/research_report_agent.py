import json
import logging
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.rag.llm_service import ask_llm
from app.models.research_report import ResearchReport
from app.models.post import Post
from app.models.timeline_event import TimelineEvent

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """Attempt to extract and parse JSON from LLM output, handling markdown blocks."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()
    return json.loads(text)


# =====================================================================
# SUB-AGENTS (No LLM)
# =====================================================================

def news_agent(db: Session, entity: str) -> list:
    """
    Sub-Agent 1: News Agent.
    Retrieves the 10 most recent posts mentioning the entity.
    """
    pattern = f"%{entity.lower()}%"
    posts = (
        db.query(Post)
        .filter(
            (Post.title.ilike(pattern)) |
            (Post.content.ilike(pattern))
        )
        .order_by(Post.posted_at.desc())
        .limit(10)
        .all()
    )
    return posts


def sentiment_agent_sub(posts: list) -> dict:
    """
    Sub-Agent 2: Sentiment Agent.
    Aggregates sentiment counts and average scores for the news set.
    """
    bullish = sum(1 for p in posts if (p.sentiment or "").upper() == "BULLISH")
    bearish = sum(1 for p in posts if (p.sentiment or "").upper() == "BEARISH")
    neutral = sum(1 for p in posts if (p.sentiment or "").upper() == "NEUTRAL" or not p.sentiment)
    total = len(posts)

    avg_importance = int(sum(p.importance_score for p in posts if p.importance_score) / len(posts)) if posts else 50

    return {
        "total_articles": total,
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
        "average_importance": avg_importance
    }


def entity_agent_sub(posts: list, target_entity: str) -> list:
    """
    Sub-Agent 3: Entity Agent.
    Extracts other entities that co-occur in the same articles as the target entity.
    """
    co_occurring = set()
    for p in posts:
        if p.entities:
            for cat in ["companies", "people", "countries", "sectors", "assets"]:
                items = p.entities.get(cat, [])
                if isinstance(items, list):
                    for item in items:
                        if item.lower().strip() != target_entity.lower().strip():
                            co_occurring.add(f"{item} ({cat[:-1]})")
    return list(co_occurring)[:15]


def timeline_agent_sub(db: Session, entity: str) -> list:
    """
    Sub-Agent 4: Timeline Agent.
    Retrieves the stored chronological events list for this entity.
    """
    events = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.entity_name.ilike(entity.strip()))
        .order_by(TimelineEvent.event_date.asc())
        .limit(8)
        .all()
    )
    return [
        f"{e.event_date.strftime('%b %d, %Y')}: {e.event_title} - {e.description}"
        for e in events
    ]


def risk_agent_sub(posts: list) -> list:
    """
    Sub-Agent 5: Risk Agent.
    Extracts negative sentiment indicators and risk themes from news items.
    """
    risks = []
    for p in posts:
        if (p.sentiment or "").upper() == "BEARISH":
            risks.append(f"Bearish Event: {p.title} (Reason: {p.reasoning or 'market risk'})")
        elif p.importance_score and p.importance_score >= 80:
            if "regulation" in (p.event_type or "").lower() or "policy" in (p.event_type or "").lower():
                risks.append(f"Policy Impact: {p.title}")
    return risks[:5]


# =====================================================================
# COORDINATOR AGENT
# =====================================================================

def generate_research_report(db: Session, entity_name: str, force: bool = False) -> ResearchReport:
    """
    Checks the database cache first. If a report was generated for the target entity
    in the last 6 hours and force=False, returns it immediately.
    Otherwise, runs 5 sub-agents to synthesize an in-depth AI research report using Groq.
    """
    entity_name = entity_name.strip()

    if not force:
        # Check cache (6 hours TTL)
        cache_limit = datetime.utcnow() - timedelta(hours=6)
        cached_report = (
            db.query(ResearchReport)
            .filter(
                ResearchReport.entity_name.ilike(entity_name),
                ResearchReport.created_at >= cache_limit
            )
            .order_by(ResearchReport.created_at.desc())
            .first()
        )
        if cached_report:
            logger.info(f"[CACHE HIT] Research report for '{entity_name}' loaded from DB cache (TTL 6h).")
            return cached_report

    logger.info(f"Generating research report via single synthesis LLM call for: {entity_name}")

    # Run sub-agents locally (No LLM calls)
    posts = news_agent(db, entity_name)
    sentiment_data = sentiment_agent_sub(posts)
    entities_data = entity_agent_sub(posts, entity_name)
    timeline_data = timeline_agent_sub(db, entity_name)
    risks_data = risk_agent_sub(posts)

    # Format news items for the LLM
    news_summaries = [
        f"- {p.title} (Source: {p.source_id}, Sentiment: {p.sentiment or 'NEUTRAL'}, Importance: {p.importance_score or 50})"
        for p in posts
    ]

    prompt = f"""You are the Lead Investment Coordinator Agent.
Synthesize the sub-agent data below to create a professional Research Report for "{entity_name}".

SUB-AGENT INPUTS:

1. NEWS AGENT: Recent news items:
{json.dumps(news_summaries, indent=2)}

2. SENTIMENT AGENT: Aggregated metrics:
{json.dumps(sentiment_data, indent=2)}

3. ENTITY RELATIONSHIP AGENT: Co-occurring entities:
{json.dumps(entities_data, indent=2)}

4. TIMELINE AGENT: Chronological events:
{json.dumps(timeline_data, indent=2)}

5. RISK AGENT: Risk indicators:
{json.dumps(risks_data, indent=2)}

Synthesize these inputs into a structured report. Return ONLY a valid JSON object in this exact format:
{{
  "executive_summary": "3-4 sentence high-level synthesis of findings and investment opinion.",
  "recent_news": [
    "Brief summary of recent headline events and their relevance.",
    "Another brief news narrative point."
  ],
  "sentiment_analysis": "Comprehensive analysis of sentiment metrics, market bias, and investor conviction.",
  "historical_timeline": [
    "Chronological event summary 1",
    "Chronological event summary 2"
  ],
  "opportunities": [
    "Opportunity statement based on positive news and relations.",
    "Another potential market opportunity."
  ],
  "risks": [
    "Risk statement 1 based on bearish metrics or regulatory developments.",
    "Risk statement 2."
  ],
  "overall_rating": "BUY|HOLD|SELL|ACCUMULATE|NEUTRAL"
}}

Rules:
- Make sure the rating aligns with the sentiment metrics.
- Keep all fields written in clean, premium financial markdown syntax (bolding, percentages where useful).
"""

    try:
        response = ask_llm(prompt, article_title=f"Research Report: {entity_name}", attempt=1)
        report_data = extract_json(response)

        report = ResearchReport(
            id=uuid.uuid4(),
            entity_name=entity_name,
            report_data=report_data
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info(f"Research report successfully generated and saved for {entity_name}")
        return report

    except Exception as e:
        logger.error(f"Failed to generate research report: {e}")
        # Fallback report
        fallback_data = {
            "executive_summary": f"Fallback report generated for {entity_name} due to compiler error.",
            "recent_news": [p.title for p in posts[:3]],
            "sentiment_analysis": f"Recent sentiment data: {sentiment_data}",
            "historical_timeline": timeline_data or ["No timeline events found."],
            "opportunities": [f"Potential opportunity in the {entity_name} ecosystem."],
            "risks": [f"Technical/LLM error: {e}"],
            "overall_rating": "NEUTRAL"
        }
        report = ResearchReport(
            id=uuid.uuid4(),
            entity_name=entity_name,
            report_data=fallback_data
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
