"""
Smart alert generation.

Can be run manually:
    python -m app.scripts.generate_alerts

Or called programmatically via generate_alerts(db).

Scalability note
----------------
The previous implementation loaded every user and every post and executed a
duplicate-check query for each (user, post) pair on every 10-minute cycle --
O(users x posts) queries, rescanning the entire post history forever.

This version:
  * selects only posts that have not yet been through alert generation
    (Post.alerts_processed_at IS NULL) and that actually qualify,
  * loads existing alert keys for the affected posts in ONE query,
  * builds all new Alert rows in memory and inserts them in a single batch,
  * marks the processed posts and commits once,
  * dispatches notification channels only after the commit succeeds.

The observable behaviour (which posts generate alerts, for which users) is
unchanged.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.models.post import Post
from app.models.alert import Alert
from app.services.alert_engine import (
    qualifies_for_alert,
    build_alert,
    dispatch_alert_notifications,
)

logger = logging.getLogger(__name__)

# Upper bound on posts handled per run, so a large backlog is drained across
# several cycles instead of blocking one very long run.
MAX_POSTS_PER_RUN = 500


def generate_alerts(db: Session, max_posts: int = MAX_POSTS_PER_RUN) -> int:
    """
    Generate alerts for posts that have not yet been processed.
    Returns the number of NEW alerts created.
    """
    candidate_posts = (
        db.query(Post)
        .filter(
            Post.alerts_processed_at.is_(None),
            Post.importance_score.isnot(None),   # not yet enriched -> not ready
        )
        .order_by(Post.posted_at.desc())
        .limit(max_posts)
        .all()
    )

    if not candidate_posts:
        logger.info("generate_alerts: no unprocessed posts in queue.")
        return 0

    user_ids = [u.id for u in db.query(User.id).all()]
    if not user_ids:
        # No users yet: still mark posts processed so they are not rescanned.
        _mark_processed(db, candidate_posts)
        db.commit()
        logger.info("generate_alerts: no users; marked %d posts processed.", len(candidate_posts))
        return 0

    qualifying_posts = [p for p in candidate_posts if qualifies_for_alert(p)]

    new_alerts: list[Alert] = []

    if qualifying_posts:
        post_ids = [p.id for p in qualifying_posts]
        titles = [p.title for p in qualifying_posts if p.title]

        # One query for existing (user_id, post_id) pairs...
        existing_pairs = set(
            db.query(Alert.user_id, Alert.post_id)
            .filter(Alert.post_id.in_(post_ids))
            .all()
        )
        # ...and one for legacy rows that predate post_id being populated.
        existing_titles = set()
        if titles:
            existing_titles = set(
                db.query(Alert.user_id, Alert.title)
                .filter(Alert.title.in_(titles))
                .all()
            )

        for post in qualifying_posts:
            for user_id in user_ids:
                if (user_id, post.id) in existing_pairs:
                    continue
                if post.title and (user_id, post.title) in existing_titles:
                    continue

                new_alerts.append(build_alert(post, user_id))
                # Guard against duplicates inside this same batch.
                existing_pairs.add((user_id, post.id))

    # Single transaction: insert alerts and mark posts processed together, so a
    # failure cannot leave posts marked done with no alerts written.
    try:
        if new_alerts:
            db.bulk_save_objects(new_alerts)
        _mark_processed(db, candidate_posts)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("generate_alerts: batch insert failed; no posts marked processed.")
        raise

    logger.info(
        "generate_alerts: created %d new alerts from %d posts (%d qualifying).",
        len(new_alerts), len(candidate_posts), len(qualifying_posts),
    )

    _dispatch_new_alerts(db, new_alerts, qualifying_posts)

    return len(new_alerts)


def _mark_processed(db: Session, posts: list) -> None:
    """Stamp posts as handled by the alert pipeline (single UPDATE)."""
    if not posts:
        return
    now = datetime.utcnow()
    db.query(Post).filter(Post.id.in_([p.id for p in posts])).update(
        {Post.alerts_processed_at: now},
        synchronize_session=False,
    )


def _dispatch_new_alerts(db: Session, new_alerts: list, qualifying_posts: list) -> None:
    """
    Fire notification channels for the alerts that were just committed.

    Runs after the commit so an email/push failure can never roll back alert
    rows, and so no notification is sent for an alert that was not persisted.
    Only the alerts created in THIS run are dispatched.
    """
    if not new_alerts:
        return

    posts_by_id = {p.id: p for p in qualifying_posts}

    for alert in new_alerts:
        try:
            dispatch_alert_notifications(db, alert, posts_by_id.get(alert.post_id))
        except Exception:
            logger.exception("generate_alerts: dispatch failed for alert %s", alert.id)


# -- manual run ---------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        total = generate_alerts(db)
        print(f"Created {total} alerts")
    finally:
        db.close()
