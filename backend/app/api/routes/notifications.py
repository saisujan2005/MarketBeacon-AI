from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
import logging

from app.db.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.models.notification_summary import NotificationSummary
from app.models.post import Post
from app.rag.llm_service import ask_llm

router = APIRouter(tags=["Notifications"])
logger = logging.getLogger(__name__)


@router.get("/notifications")
@router.get("/api/notifications")
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(
            func.coalesce(
                Notification.posted_at,
                Notification.fetched_at,
                Notification.created_at
            ).desc()
        )
        .all()
    )

    return [
        {
            "id": str(n.id),
            "keyword": n.keyword,
            "title": n.title,
            "is_read": n.is_read,
            "posted_at": n.posted_at.isoformat() if n.posted_at else None,
            "fetched_at": n.fetched_at.isoformat() if n.fetched_at else None,
            "source": n.source,
            "sentiment": n.sentiment,
            "event_type": n.event_type,
            "importance_score": n.importance_score,
            "post_url": n.post_url,
            "meta_info": n.meta_info
        }
        for n in notifications
    ]


@router.patch("/notifications/{notification_id}/read")
@router.patch("/api/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}


@router.post("/notifications/{notification_id}/summarize")
@router.post("/api/notifications/{notification_id}/summarize")
def summarize_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # 1. Check cached summaries in notification_summaries table
    cached = db.query(NotificationSummary).filter(NotificationSummary.notification_id == notification.id).first()
    if cached:
        logger.info(f"Returning cached AI summary for notification: '{notification.title}'")
        return {"summary": cached.summary}

    # 2. Match corresponding Post
    post = None
    if notification.post_url:
        post = db.query(Post).filter(Post.post_url == notification.post_url).first()
    if not post:
        post = db.query(Post).filter(Post.title == notification.title).first()

    content = post.content if post and post.content else "No detailed content available."

    # 3. Formulate the LLM Prompt
    prompt = f"""You are a financial analysis assistant. Analyze this financial news article.

Provide an explanation containing exactly these six sections, formatted with these headers:

What Happened:
[Provide a clear, one-sentence description of the event]

Why It Matters:
[Explain the underlying financial/economic significance in one sentence]

Market Impact:
[List the likely immediate sentiment direction for 2-3 relevant assets, sectors, or currencies in bullet points, e.g. • INR: Potentially supportive]

Trading Implications:
[Explain specific tactical/strategic actions a trader might take in one sentence]

Key Takeaway:
[Provide a one-sentence final conclusion/outlook]

Risk Factors:
[List 1-2 major risk factors or uncertainties associated with this event in bullet points]

Format the output cleanly. Do not include markdown code block formatting (like ```) or extra conversational text.

News Title: {notification.title}
News Content: {content}
Sentiment: {notification.sentiment or 'NEUTRAL'}
Event Type: {notification.event_type or 'OTHER'}
"""
    try:
        logger.info(f"Generating new AI summary for notification: '{notification.title}'")
        summary = ask_llm(prompt, article_title=notification.title or "Unknown")

        if not summary or len(summary.strip()) == 0:
            raise Exception("Empty response from LLM service.")

        # 4. Save to cache table
        cached_summary = NotificationSummary(
            notification_id=notification.id,
            summary=summary,
            model_used="llama-3.3-70b-versatile"
        )
        db.add(cached_summary)
        db.commit()

        return {"summary": summary}
    except Exception as llm_err:
        db.rollback()
        logger.error(f"Failed to generate summary via LLM: {llm_err}")
        raise HTTPException(status_code=500, detail="Unable to generate summary. Please try again.")