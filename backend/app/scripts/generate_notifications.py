"""
Notification generation script.

Can be run manually:
    python -m app.scripts.generate_notifications

Or called programmatically via generate_notifications(db).
"""

import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.alert import Alert
from app.models.watchlist import Watchlist
from app.models.notification import Notification
from app.agents.watchlist_agent import match_watchlist

logger = logging.getLogger(__name__)


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

            notification = Notification(
                keyword=keyword,
                title=alert.title
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