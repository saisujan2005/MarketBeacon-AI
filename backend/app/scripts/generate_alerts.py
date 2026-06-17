"""
Alert generation script.

Can be run manually:
    python -m app.scripts.generate_alerts

Or called programmatically via generate_alerts(db).
"""

import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.post import Post
from app.models.alert import Alert
from app.agents.alert_agent import should_alert

logger = logging.getLogger(__name__)


def generate_alerts(db: Session) -> int:
    """
    Scan all posts, create Alert rows for anything
    above the importance threshold that isn't already alerted.
    Returns the number of new alerts created.
    """
    posts = db.query(Post).all()
    count = 0

    for post in posts:

        if not should_alert(post.importance_score):
            continue

        existing = (
            db.query(Alert)
            .filter(Alert.title == post.title)
            .first()
        )

        if existing:
            continue

        alert = Alert(
            title=post.title,
            event_type=post.event_type,
            importance_score=str(post.importance_score)
        )

        db.add(alert)
        count += 1

    db.commit()
    logger.info(f"generate_alerts: created {count} new alerts")
    return count


# ── manual run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        total = generate_alerts(db)
        print(f"Created {total} alerts")
    finally:
        db.close()