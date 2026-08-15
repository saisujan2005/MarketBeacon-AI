import logging
import uuid
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert

logger = logging.getLogger(__name__)


def qualifies_for_alert(post) -> bool:
    """
    Single source of truth for the alert threshold.

    A post triggers an alert when its importance score exceeds the configured
    threshold (80, unchanged from the previous hardcoded value) or its impact
    level is CRITICAL.
    """
    score = post.importance_score or 0
    level = post.impact_level or "LOW"
    return score > settings.ALERT_IMPORTANCE_THRESHOLD or level == "CRITICAL"


def build_alert(post, user_id) -> Alert:
    """Constructs (without persisting) an Alert row for a post/user pair."""
    return Alert(
        id=uuid.uuid4(),
        user_id=user_id,
        title=post.title,
        event_type=post.event_type or "OTHER",
        importance_score=post.importance_score or 0,
        post_id=post.id,
        post_url=post.post_url,
    )


def send_email_alert(post) -> None:
    """
    Mock email channel architecture. Logs an email payload ready for SMTP/API integration.
    """
    logger.info(
        f"\n"
        f"=================== EMAIL ALERT OUTBOX ===================\n"
        f"Subject: HIGH IMPACT ALERT: {post.title}\n"
        f"Importance Score: {post.importance_score} / 100\n"
        f"Impact Level: {post.impact_level}\n"
        f"Sentiment: {post.sentiment or 'NEUTRAL'}\n"
        f"Reasoning: {post.sentiment_reasoning or post.reasoning or 'No explanation'}\n"
        f"==========================================================\n"
    )


def dispatch_alert_notifications(db: Session, alert: Alert, post) -> None:
    """
    Fires the email and web-push channels for an alert that has already been
    committed. Kept separate from persistence so a channel failure can never
    roll back (or duplicate) the alert row itself.
    """
    try:
        from app.models.user import User
        from app.models.push_subscription import PushSubscription
        from app.services.notification_service import (
            dispatch_smart_alert,
            dispatch_push,
            should_dispatch_push,
        )

        user = db.query(User).filter(User.id == alert.user_id).first()
        if not user:
            return

        dispatch_smart_alert(user, alert)

        if should_dispatch_push(user.preferences, "smart_alerts"):
            subs = db.query(PushSubscription).filter(
                PushSubscription.user_id == alert.user_id
            ).all()
            for sub in subs:
                dispatch_push(
                    subscription=sub,
                    title=f"Smart Alert: {alert.title[:45]}...",
                    body=f"Importance: {alert.importance_score} | Event: {alert.event_type}",
                    target_url="/alerts",
                )
    except Exception as e:
        logger.error(f"Failed to dispatch smart alert notifications: {e}")

    if post is not None:
        send_email_alert(post)


def process_post_alerts(db: Session, post, user_id) -> Alert:
    """
    Creates an alert for a single post/user pair if the post qualifies and no
    alert already exists.

    Retained for backwards compatibility and single-item use (e.g. tests). The
    scheduled pipeline uses the batched path in scripts/generate_alerts.py.
    Returns the newly created Alert, or None if nothing new was created.
    """
    if not qualifies_for_alert(post):
        return None

    existing = (
        db.query(Alert)
        .filter(Alert.user_id == user_id, Alert.post_id == post.id)
        .first()
    )
    if existing:
        return None

    # Legacy rows created before post_id was populated are matched by title.
    existing_by_title = (
        db.query(Alert)
        .filter(Alert.user_id == user_id, Alert.title == post.title)
        .first()
    )
    if existing_by_title:
        return None

    logger.info(
        f"Smart Alert triggered for user {user_id}: {post.title} "
        f"(Score: {post.importance_score}, Impact: {post.impact_level})"
    )

    alert = build_alert(post, user_id)
    db.add(alert)
    db.commit()

    dispatch_alert_notifications(db, alert, post)
    return alert
