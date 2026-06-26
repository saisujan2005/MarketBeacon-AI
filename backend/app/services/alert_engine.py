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


def process_post_alerts(db: Session, post, user_id) -> Alert:
    """
    Scans a newly enriched post and generates alerts if:
    importance_score > 80 OR impact_level == 'CRITICAL'.
    Saves the alert history and triggers email dispatch.
    """
    score = post.importance_score or 0
    level = post.impact_level or "LOW"

    if score > 80 or level == "CRITICAL":
        # Avoid duplicate alerts for the same post title and user
        existing = db.query(Alert).filter(Alert.title == post.title, Alert.user_id == user_id).first()
        if existing:
            return existing

        logger.info(f"🚨 Smart Alert Triggered for user {user_id}: {post.title} (Score: {score}, Impact: {level})")

        alert = Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            title=post.title,
            event_type=post.event_type or "OTHER",
            importance_score=str(score),
            post_id=post.id,
            post_url=post.post_url
        )
        db.add(alert)
        db.commit()

        # Send alert via email and push channels
        try:
            from app.models.user import User
            from app.models.push_subscription import PushSubscription
            from app.services.notification_service import dispatch_smart_alert, dispatch_push
            
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Dispatch Email
                dispatch_smart_alert(user, alert)
                
                # Dispatch Web Push if preference enabled
                from app.services.notification_service import should_dispatch_push
                if should_dispatch_push(user.preferences, "smart_alerts"):
                    subs = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
                    for sub in subs:
                        dispatch_push(
                            subscription=sub,
                            title=f"Smart Alert: {alert.title[:45]}...",
                            body=f"Importance: {alert.importance_score} | Event: {alert.event_type}",
                            target_url="/alerts"
                        )
        except Exception as e:
            logger.error(f"Failed to dispatch smart alert notifications: {e}")

        send_email_alert(post)
        return alert

    return None
