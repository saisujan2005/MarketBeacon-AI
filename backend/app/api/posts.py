from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.post import Post
from app.schemas.post import PostResponse

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


@router.get("/", response_model=list[PostResponse])
def get_posts(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit

    posts = (
        db.query(Post)
        .order_by(Post.fetched_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return posts