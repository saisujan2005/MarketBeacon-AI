from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.dependencies import get_current_user
from app.models.user import User
from app.agents.daily_briefing_agent import (
    generate_daily_briefing,
    get_latest_briefing,
    get_briefing_history
)

router = APIRouter(tags=["Daily Briefing"])


@router.get("/daily-briefing/latest")
@router.get("/api/daily-briefing/latest")
def get_latest(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns the latest morning briefing for the authenticated user.
    """
    briefing = get_latest_briefing(db, user_id=current_user.id)
    return {
        "id": str(briefing.id),
        "created_at": briefing.created_at.isoformat(),
        "top_events": briefing.top_events,
        "bullish_sectors": briefing.bullish_sectors,
        "bearish_sectors": briefing.bearish_sectors,
        "market_summary": briefing.market_summary,
        "outlook": briefing.outlook
    }


@router.get("/daily-briefing/history")
@router.get("/api/daily-briefing/history")
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns past briefings list for the authenticated user.
    """
    history = get_briefing_history(db, user_id=current_user.id, limit=10)
    return [
        {
            "id": str(b.id),
            "created_at": b.created_at.isoformat(),
            "top_events": b.top_events,
            "bullish_sectors": b.bullish_sectors,
            "bearish_sectors": b.bearish_sectors,
            "market_summary": b.market_summary,
            "outlook": b.outlook
        }
        for b in history
    ]


@router.post("/daily-briefing/generate")
@router.post("/api/daily-briefing/generate")
def generate_new(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Triggers generation of a new daily briefing for the authenticated user.
    """
    briefing = generate_daily_briefing(db, user_id=current_user.id, force=True)
    return {
        "message": "Daily briefing generated successfully.",
        "briefing": {
            "id": str(briefing.id),
            "created_at": briefing.created_at.isoformat(),
            "top_events": briefing.top_events,
            "bullish_sectors": briefing.bullish_sectors,
            "bearish_sectors": briefing.bearish_sectors,
            "market_summary": briefing.market_summary,
            "outlook": briefing.outlook
        }
    }


@router.post("/brief/generate")
@router.post("/api/brief/generate")
def generate_market_brief(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Analyzes latest user-specific alerts, notifications, and global posts to generate an AI Daily Brief.
    """
    from app.models.alert import Alert
    from app.models.notification import Notification
    from app.models.post import Post
    from app.rag.llm_service import ask_llm

    # Fetch latest 10 of each (alerts and notifications filtered by current user)
    alerts = db.query(Alert).filter(Alert.user_id == current_user.id).order_by(Alert.created_at.desc()).limit(10).all()
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    posts = db.query(Post).order_by(Post.posted_at.desc()).limit(10).all()

    alerts_str = "\n".join([f"- {a.title} (Importance: {a.importance_score})" for a in alerts])
    notifications_str = "\n".join([f"- {n.title} (Source: {n.source})" for n in notifications])
    posts_str = "\n".join([f"- {p.title} (Sentiment: {p.sentiment})" for p in posts])

    prompt = f"""You are a senior financial analyst at MarketBeacon.
Analyze the following latest market events, notifications, and news items to generate a daily market brief.

Latest Alerts:
{alerts_str or "No alerts."}

Latest Notifications:
{notifications_str or "No notifications."}

Latest News:
{posts_str or "No news."}

Generate the MARKETBEACON DAILY BRIEF in this EXACT text format:

MARKETBEACON DAILY BRIEF

Top Events
1. [Event Title 1]
2. [Event Title 2]
3. [Event Title 3]

Market Mood
[Mood description, e.g. Neutral / Bullish / Bearish]

Key Risks
- [Risk 1]
- [Risk 2]

Trading Opportunities
- [Opportunity 1]
- [Opportunity 2]

Watch Tomorrow
- [What to watch 1]
- [What to watch 2]

Keep the brief concise, professional, and trader-focused. Ensure the heading "MARKETBEACON DAILY BRIEF" is exactly at the top.
"""

    try:
        brief_text = ask_llm(prompt, article_title="Daily Market Brief")
        return {"brief": brief_text}
    except Exception as e:
        # Fallback response in case of API limits or LLM offline
        fallback_brief = f"""MARKETBEACON DAILY BRIEF

Top Events
1. Rate policy debates
2. Global market flow fluctuations
3. Regional banking reports

Market Mood
Neutral

Key Risks
- High rate environment impacts bond pricing
- Regulatory changes in banking sectors

Trading Opportunities
- Defensive plays in Large Cap banks
- Shorter term trade options in commodities

Watch Tomorrow
- Federal Reserve upcoming statements
- Daily volume swings in key sectors
"""
        return {"brief": fallback_brief, "warning": f"AI brief compilation error: {str(e)}"}
