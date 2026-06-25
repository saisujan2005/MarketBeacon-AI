from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db, SessionLocal
from app.models.post import Post
from app.scripts.score_posts import score_posts
from app.scripts.generate_alerts import generate_alerts
from app.scripts.generate_notifications import generate_notifications

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


def reprocess_job():
    db = SessionLocal()
    try:
        logger.info("Starting manual reprocessing of all posts...")
        # Reset posts scoring fields
        db.query(Post).update({
            Post.importance_score: None,
            Post.sentiment: None,
            Post.sentiment_confidence: None,
            Post.sentiment_reasoning: None,
            Post.event_type: None,
            Post.predicted_direction: None,
            Post.prediction_confidence: None,
            Post.prediction_reasoning: None,
            Post.impact_level: None,
        })
        db.commit()
        
        # Re-run scoring pipeline
        processed = score_posts(db)
        logger.info(f"Reprocessing complete. Scored {processed} posts.")
        
        # Re-run alerts and notifications
        alerts = generate_alerts(db)
        notifications = generate_notifications(db)
        logger.info(f"Generated {alerts} alerts and {notifications} notifications.")
        
    except Exception as e:
        logger.error(f"Error during manual reprocessing: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/reprocess-posts")
def trigger_reprocess_posts_post(background_tasks: BackgroundTasks):
    background_tasks.add_task(reprocess_job)
    return {"message": "Reprocessing started in the background (POST)."}


@router.get("/reprocess-posts")
def trigger_reprocess_posts_get(background_tasks: BackgroundTasks):
    background_tasks.add_task(reprocess_job)
    return {"message": "Reprocessing started in the background (GET)."}
