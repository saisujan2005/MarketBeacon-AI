from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.dependencies import get_current_user
from app.models.post import Post
from app.models.user import User

router = APIRouter()


@router.get("/trends")
def get_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a count of posts per event type.

    Aggregation is performed in SQL rather than loading every post into memory.
    """
    rows = (
        db.query(Post.event_type, func.count(Post.id))
        .group_by(Post.event_type)
        .all()
    )

    return {event_type: count for event_type, count in rows}
