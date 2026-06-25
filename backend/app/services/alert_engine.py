import logging
import uuid
from sqlalchemy.orm import Session
from app.models.alert import Alert

logger = logging.getLogger(__name__)


def send_email_alert(post) -> None:
    """
    Mock email channel architecture. Logs an email payload ready for SMTP/API integration.
    """
    logger.info(
        f"\n"
        f"=================== EMAIL ALERT OUTBOX ===================\n"
        f"Subject: 🚨 HIGH IMPACT ALERT: {post.title}\n"
        f"Importance Score: {post.importance_score} / 100\n"
        f"Impact Level: {post.impact_level}\n"
        f"Sentiment: {post.sentiment or 'NEUTRAL'}\n"
        f"Reasoning: {post.sentiment_reasoning or post.reasoning or 'No explanation'}\n"
        f"==========================================================\n"
    )


def process_post_alerts(db: Session, post) -> Alert:
    """
    Scans a newly enriched post and generates alerts if:
    importance_score > 80 OR impact_level == 'CRITICAL'.
    Saves the alert history and triggers email dispatch.
    """
    score = post.importance_score or 0
    level = post.impact_level or "LOW"

    if score > 80 or level == "CRITICAL":
        # Avoid duplicate alerts for the same post title
        existing = db.query(Alert).filter(Alert.title == post.title).first()
        if existing:
            return existing

        logger.info(f"🚨 Smart Alert Triggered: {post.title} (Score: {score}, Impact: {level})")

        alert = Alert(
            id=uuid.uuid4(),
            title=post.title,
            event_type=post.event_type or "OTHER",
            importance_score=str(score),
            post_id=post.id,
            post_url=post.post_url
        )
        db.add(alert)
        db.commit()

        # Send alert via email channel
        send_email_alert(post)
        return alert

    return None
