"""
Scores all unscored posts with an importance score.

Can be run manually:
    python -m app.scripts.score_posts

Or called programmatically via score_posts(db).
"""

import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.post import Post
from app.agents.importance_agent import score_event

logger = logging.getLogger(__name__)


def score_posts(db: Session) -> int:
    """
    Find all posts with importance_score = None and score them.
    Returns the number of posts scored.
    """
    unscored = (
        db.query(Post)
        .filter(Post.importance_score == None)  # noqa: E711
        .all()
    )

    count = 0
    for post in unscored:
        post.importance_score = score_event(post.event_type)
        count += 1

    db.commit()
    logger.info(f"score_posts: scored {count} posts")
    return count


# ── manual run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        total = score_posts(db)
        print(f"Scored {total} posts")
    finally:
        db.close()