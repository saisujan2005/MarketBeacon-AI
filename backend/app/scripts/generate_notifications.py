"""
Notification generation script.

Can be run manually:
    python -m app.scripts.generate_notifications

Or called programmatically via generate_notifications(db).
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.alert import Alert
from app.models.post import Post
from app.models.watchlist import Watchlist
from app.models.notification import Notification
from app.agents.watchlist_agent import match_watchlist

logger = logging.getLogger(__name__)


def find_matching_post(db: Session, alert):
    # 1. Match by alert.post_id if available
    if hasattr(alert, 'post_id') and alert.post_id:
        post = db.query(Post).filter(Post.id == alert.post_id).first()
        if post:
            return post, "post_id", 100
            
    # 2. Match by alert.post_url if available
    if hasattr(alert, 'post_url') and alert.post_url:
        post = db.query(Post).filter(Post.post_url == alert.post_url).first()
        if post:
            return post, "post_url", 100
            
    # 3. Match by title
    posts = db.query(Post).filter(Post.title == alert.title).all()
    if not posts:
        return None, "none", 0
        
    if len(posts) == 1:
        return posts[0], "unique_title", 85
        
    # Match by event_type if multiple posts have the same title
    for post in posts:
        if post.event_type == alert.event_type:
            return post, "title_and_event_type", 95
            
    return posts[0], "title_fallback", 70


def generate_notifications(db: Session) -> int:
    """
    For every alert, check if its title matches any watchlist keyword.
    Create a Notification row for each match that doesn't already exist.
    Returns the number of new notifications created.
    """
    alerts = db.query(Alert).all()
    watchlists = db.query(Watchlist).all()
    keywords = [w.keyword for w in watchlists]

    created = 0

    for alert in alerts:

        matches = match_watchlist(alert.title, keywords)

        for keyword in matches:

            existing = (
                db.query(Notification)
                .filter(
                    Notification.keyword == keyword,
                    Notification.title == alert.title
                )
                .first()
            )

            if existing:
                continue

            post, match_method, confidence = find_matching_post(db, alert)
            
            def ensure_utc(dt):
                if dt is None:
                    return None
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)

            posted_at = ensure_utc(post.posted_at) if post else None
            fetched_at = ensure_utc(post.fetched_at) if post else ensure_utc(alert.created_at)
            source = post.source_id if post else None
            sentiment = post.sentiment if post else None
            event_type = post.event_type if post else alert.event_type
            post_url = post.post_url if post else (alert.post_url if hasattr(alert, 'post_url') else None)
            
            importance_score = None
            if post and post.importance_score is not None:
                importance_score = post.importance_score
            else:
                try:
                    importance_score = int(alert.importance_score) if alert.importance_score else None
                except ValueError:
                    pass

            if post:
                logger.info(f"Matched Alert '{alert.title}' to Post ID {post.id} using {match_method} with {confidence}% confidence.")
            else:
                logger.warning(f"Could not match Alert '{alert.title}' to any Post. Using fallback alert metadata.")

            notification = Notification(
                keyword=keyword,
                title=alert.title,
                posted_at=posted_at,
                fetched_at=fetched_at,
                source=source,
                sentiment=sentiment,
                event_type=event_type,
                importance_score=importance_score,
                post_url=post_url,
                meta_info={
                    "match_method": match_method,
                    "confidence": confidence,
                    "source_type": "rss_post" if post else "alert_fallback"
                }
            )

            db.add(notification)
            created += 1

    db.commit()
    logger.info(f"generate_notifications: created {created} new notifications")
    return created



# ── manual run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        total = generate_notifications(db)
        print(f"Created {total} notifications")
    finally:
        db.close()