from fastapi import APIRouter
from sqlalchemy import func

from app.db.database import SessionLocal
from app.models.post import Post

router = APIRouter()


@router.get("/market-summary")
def market_summary():
    db = SessionLocal()

    try:
        # Get important news items (importance_score >= 70) sorted by newest first
        posts = (
            db.query(Post)
            .filter(Post.importance_score >= 70)
            .order_by(func.coalesce(Post.posted_at, Post.fetched_at).desc())
            .all()
        )

        return {
            "summary": [
                {
                    "id": str(post.id),
                    "title": post.title,
                    "event_type": post.event_type,
                    "importance_score": post.importance_score,
                    "impact_level": post.impact_level,
                    "reasoning": post.reasoning,
                    "confidence": post.confidence,
                    "affected_assets": post.affected_assets,
                    "sentiment": post.sentiment,
                    "sentiment_confidence": post.sentiment_confidence,
                    "sentiment_reasoning": post.sentiment_reasoning,
                    "predicted_direction": post.predicted_direction,
                    "prediction_confidence": post.prediction_confidence,
                    "prediction_reasoning": post.prediction_reasoning,
                    "entities": post.entities,
                    "post_url": post.post_url,
                    "source_id": post.source_id,
                    # Ensure ISO strings are timezone-aware UTC by appending 'Z'
                    "posted_at": post.posted_at.isoformat() + "Z" if post.posted_at else None,
                    "fetched_at": post.fetched_at.isoformat() + "Z" if post.fetched_at else None
                }
                # Limit to top 15 most recent important articles
                for post in posts[:15]
            ]
        }

    finally:
        db.close()