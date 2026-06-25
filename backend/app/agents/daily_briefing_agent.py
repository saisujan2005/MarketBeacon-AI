import json
import logging
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.rag.llm_service import ask_llm
from app.models.daily_briefing import DailyBriefing
from app.models.post import Post

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """Attempt to extract and parse JSON from LLM output, handling markdown blocks."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()
    return json.loads(text)


def generate_daily_briefing(db: Session, user_id: uuid.UUID, force: bool = False) -> DailyBriefing:
    """
    Checks the database cache for the user first. If a briefing was generated in the last 24 hours
    and force=False, returns it immediately.
    Otherwise, aggregates the last 100 articles and compiles the briefing.
    """
    if not force:
        # Check cache (24 hours TTL) for this user
        cache_limit = datetime.utcnow() - timedelta(hours=24)
        cached_briefing = (
            db.query(DailyBriefing)
            .filter(DailyBriefing.user_id == user_id, DailyBriefing.created_at >= cache_limit)
            .order_by(DailyBriefing.created_at.desc())
            .first()
        )
        if cached_briefing:
            logger.info(f"[CACHE HIT] Daily briefing loaded from database cache (TTL 24h) for user {user_id}.")
            return cached_briefing

    logger.info(f"Generating daily AI briefing for user {user_id} via single aggregated LLM request...")

    # Fetch last 100 articles
    recent_posts = (
        db.query(Post)
        .order_by(Post.posted_at.desc())
        .limit(100)
        .all()
    )

    if not recent_posts:
        # No posts at all
        briefing = DailyBriefing(
            user_id=user_id,
            top_events=["No recent events available."],
            bullish_sectors=[],
            bearish_sectors=[],
            market_summary="No news data available to summarize.",
            outlook="Neutral"
        )
        db.add(briefing)
        db.commit()
        db.refresh(briefing)
        return briefing

    # Format 100 posts into context block
    news_items = []
    for idx, p in enumerate(recent_posts):
        sector_str = "OTHER"
        if p.entities and isinstance(p.entities.get("sectors"), list) and p.entities["sectors"]:
            sector_str = p.entities["sectors"][0]
        elif p.event_type:
            sector_str = p.event_type

        news_items.append(
            f"{idx+1}. Title: {p.title} | Sector: {sector_str} | Sentiment: {p.sentiment or 'NEUTRAL'} | Importance: {p.importance_score or 50}"
        )

    context_text = "\n".join(news_items)

    prompt = f"""You are an expert market analyst. Summarize the following market activity into a single, cohesive daily briefing.

RECENT ARTICLES SUMMARY:
{context_text}

Analyze the aggregate market flow and return ONLY a valid JSON object in this exact format:
{{
  "top_events": [
    "High-level event 1 (e.g. RBI unexpectedly cut the repo rate by 25bps)",
    "High-level event 2",
    "High-level event 3"
  ],
  "bullish_sectors": ["Sector1", "Sector2"],
  "bearish_sectors": ["Sector1"],
  "market_summary": "Overall market narrative summarizing the major themes and catalysts (60-80 words).",
  "outlook": "Bullish|Bearish|Neutral|Moderately Bullish|Moderately Bearish"
}}

Rules:
- Focus on the main, market-moving events from the articles list.
- Keep sector names clean (Banking, IT, Energy, Pharma, Auto, FMCG, Telecom, Metals).
"""

    try:
        response = ask_llm(prompt, article_title="Aggregated Daily Briefing", attempt=1)
        data = extract_json(response)

        top_events = data.get("top_events", [])
        bullish_sectors = data.get("bullish_sectors", [])
        bearish_sectors = data.get("bearish_sectors", [])
        market_summary = data.get("market_summary", "Summary compilation failed.")
        outlook = data.get("outlook", "Neutral")

        briefing = DailyBriefing(
            user_id=user_id,
            top_events=top_events,
            bullish_sectors=bullish_sectors,
            bearish_sectors=bearish_sectors,
            market_summary=market_summary,
            outlook=outlook
        )
        db.add(briefing)
        db.commit()
        db.refresh(briefing)
        logger.info("Daily AI briefing generated and saved successfully.")
        return briefing

    except Exception as e:
        logger.error(f"Failed to generate daily AI briefing: {e}")
        # Return fallback using first 3 articles
        fallback = DailyBriefing(
            user_id=user_id,
            top_events=[p.title for p in recent_posts[:3]],
            bullish_sectors=[],
            bearish_sectors=[],
            market_summary=f"Briefing compilation failed due to LLM error. Details: {e}",
            outlook="Neutral"
        )
        db.add(fallback)
        db.commit()
        db.refresh(fallback)
        return fallback


def get_latest_briefing(db: Session, user_id: uuid.UUID) -> DailyBriefing:
    """
    Returns the latest DailyBriefing. Automatically generates one if cached version is older than 24h.
    """
    cache_limit = datetime.utcnow() - timedelta(hours=24)
    latest = (
        db.query(DailyBriefing)
        .filter(DailyBriefing.user_id == user_id)
        .order_by(DailyBriefing.created_at.desc())
        .first()
    )

    if not latest or latest.created_at < cache_limit:
        latest = generate_daily_briefing(db, user_id=user_id)
    return latest


def get_briefing_history(db: Session, user_id: uuid.UUID, limit: int = 10) -> list:
    """
    Returns the historical briefings.
    """
    return (
        db.query(DailyBriefing)
        .filter(DailyBriefing.user_id == user_id)
        .order_by(DailyBriefing.created_at.desc())
        .limit(limit)
        .all()
    )
