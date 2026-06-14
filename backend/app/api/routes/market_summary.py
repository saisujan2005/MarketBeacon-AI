from fastapi import APIRouter

from app.db.database import SessionLocal
from app.models.post import Post

router = APIRouter()


@router.get("/market-summary")
def market_summary():

    db = SessionLocal()

    try:
        posts = (
            db.query(Post)
            .filter(Post.importance_score >= 70)
            .order_by(Post.importance_score.desc())
            .all()
        )

        return {
            "summary": [
                {
                    "title": post.title,
                    "event_type": post.event_type,
                    "importance_score": post.importance_score
                }
                for post in posts[:5]
            ]
        }

    finally:
        db.close()