from fastapi import APIRouter, Query, Depends, HTTPException, status
from typing import Optional
from sqlalchemy import cast, Integer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.dependencies import get_current_user
from app.models.user import User
from app.models.alert import Alert
from app.models.post import Post
import uuid
import json
from datetime import datetime

router = APIRouter(tags=["Alerts"])


@router.get("/alerts")
@router.get("/api/alerts")
def get_alerts(
    severity: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    importance_min: Optional[int] = Query(None),
    direction: Optional[str] = Query(None),
    sort: str = Query("latest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Join alerts with posts to get source_id and metadata, filtered by current user
    query = (
        db.query(Alert, Post)
        .outerjoin(Post, Post.title == Alert.title)
        .filter(Alert.user_id == current_user.id)
    )

    # Apply Filters
    if severity:
        query = query.filter(Post.impact_level == severity)
    if source:
        query = query.filter(Post.source_id == source)
    if importance_min is not None:
        query = query.filter(cast(Alert.importance_score, Integer) >= importance_min)
    if direction:
        if direction.upper() != "INBOUND":
            query = query.filter(False)

    # Apply Sorting
    if sort == "oldest":
        query = query.order_by(Alert.created_at.asc())
    elif sort == "importance":
        query = query.order_by(cast(Alert.importance_score, Integer).desc())
    elif sort == "confidence":
        query = query.order_by(Post.confidence.desc())
    else:
        # Default to latest
        query = query.order_by(Alert.created_at.desc())

    results = query.all()

    seen = set()
    alerts = []
    for alert, post in results:
        if alert.title in seen:
            continue
        seen.add(alert.title)
        
        created_at_str = None
        if alert.created_at:
            created_at_str = alert.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")

        alerts.append({
            "id": str(alert.id),
            "title": alert.title,
            "event_type": alert.event_type,
            "importance_score": int(alert.importance_score) if alert.importance_score else 0,
            "source_id": post.source_id if post else "unknown",
            "post_url": post.post_url if post else None,
            "impact_level": post.impact_level if post else "UNKNOWN",
            "reasoning": post.reasoning if post else "",
            "confidence": post.confidence if post else 0,
            "affected_assets": post.affected_assets if post else [],
            "created_at": created_at_str,
            "direction": "INBOUND"
        })
    return alerts


@router.post("/alerts/{alert_id}/summarize")
@router.post("/api/alerts/{alert_id}/summarize")
def summarize_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch Alert belonging to current user
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        try:
            alert_uuid = uuid.UUID(alert_id)
            alert = db.query(Alert).filter(Alert.id == alert_uuid, Alert.user_id == current_user.id).first()
        except ValueError:
            raise HTTPException(status_code=404, detail="Alert not found")

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Check Cache
    now = datetime.utcnow()
    if alert.summary_text and alert.summary_generated_at:
        age = now - alert.summary_generated_at
        if age.total_seconds() < 24 * 3600:
            try:
                return json.loads(alert.summary_text)
            except Exception:
                pass

    # Fetch related post for extra context
    post = db.query(Post).filter(Post.title == alert.title).first()
    context = post.reasoning if post else ""

    # Generate summary using LLM
    prompt = f"""You are a professional financial analyst.

Analyze the following market event.

Event Title:
{alert.title}

Event Details:
{context or 'No details provided.'}

Return ONLY a valid JSON object in this exact format:
{{
  "summary": "Executive Summary of the event...",
  "market_impact": "Key bullet points on market impact (e.g. • Banking sector stable\\n• Bond yields may soften)",
  "affected_sectors": ["Sector A", "Sector B"],
  "outlook": "Bullish/Bearish/Neutral",
  "confidence": 85,
  "key_takeaways": "Key takeaways for traders...",
  "suggested_watchlist": ["Asset/Ticker A", "Asset/Ticker B"]
}}

Keep response concise and trader-focused. Do not output anything other than raw JSON.
"""

    from app.rag.llm_service import ask_llm
    from app.agents.prediction_agent import extract_json

    try:
        response_text = ask_llm(prompt, article_title=alert.title)
        
        try:
            data = extract_json(response_text)
        except Exception:
            data = {
                "summary": response_text,
                "market_impact": "• Details in summary narrative.",
                "affected_sectors": [alert.event_type] if alert.event_type else [],
                "outlook": "Neutral",
                "confidence": 75,
                "key_takeaways": "Analyze market data closely.",
                "suggested_watchlist": []
            }

        if "key_takeaways" not in data:
            data["key_takeaways"] = "Analyze market data closely."
        if "suggested_watchlist" not in data:
            data["suggested_watchlist"] = []

        # Save to database cache
        alert.summary_text = json.dumps(data)
        alert.summary_generated_at = now
        db.commit()

        return data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.post("/alerts/summarize-bulk")
@router.post("/api/alerts/summarize-bulk")
def summarize_alerts_bulk(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert_ids = req.get("alert_ids", [])
    if not alert_ids:
        raise HTTPException(status_code=400, detail="No alert IDs provided")

    # Fetch alerts matching ids for this user
    alerts = db.query(Alert).filter(Alert.id.in_(alert_ids), Alert.user_id == current_user.id).all()
    if not alerts:
        raise HTTPException(status_code=404, detail="Alerts not found")

    titles_str = "\n".join([f"- {a.title} ({a.event_type})" for a in alerts])
    prompt = f"""You are a professional financial analyst.
Summarize the following multiple market alerts.

Alerts:
{titles_str}

Return a unified trading intelligence brief in this exact format:

Today's Market Brief

{len(alerts)} major events detected.

Key Themes:
• [Theme 1]
• [Theme 2]

Market Sentiment:
[Bullish/Bearish/Neutral]

Most Important Event:
[Brief description of the most significant event among these]
"""

    from app.rag.llm_service import ask_llm
    try:
        summary_text = ask_llm(prompt, article_title="Bulk Alert Summary")
        return {"summary": summary_text}
    except Exception as e:
        fallback_summary = f"""Today's Market Brief

{len(alerts)} major events detected.

Key Themes:
• Rate environment discussions
• Regulatory watchlists updates

Market Sentiment:
Neutral

Most Important Event:
Market developments regarding global macro variables.
"""
        return {"summary": fallback_summary, "warning": f"LLM error: {str(e)}"}