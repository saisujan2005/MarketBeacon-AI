from fastapi import APIRouter
from collections import Counter

from app.db.database import SessionLocal
from app.models.post import Post

router = APIRouter()

@router.get("/trends")
def get_trends():

    db = SessionLocal()

    posts = db.query(Post).all()

    counts = Counter(
        [
            post.event_type
            for post in posts
        ]
    )

    return dict(counts)