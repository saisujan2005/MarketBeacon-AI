"""
Smart alert generation script.

Can be run manually:
    python -m app.scripts.generate_alerts

Or called programmatically via generate_alerts(db).
"""

import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.post import Post
from app.services.alert_engine import process_post_alerts

logger = logging.getLogger(__name__)


def generate_alerts(db: Session) -> int:
    """
    Scan all posts and run them through the smart alert engine.
    Returns the number of new alerts created.
    """
    posts = db.query(Post).all()
    count = 0

    for post in posts:
        # process_post_alerts handles duplicate checking and DB insertions internally
        alert = process_post_alerts(db, post)
        if alert:
            count += 1

    logger.info(f"generate_alerts: created {count} new smart alerts")
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