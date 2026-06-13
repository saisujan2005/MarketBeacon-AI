from sqlalchemy.orm import Session
from app.models.post import Post


def save_post(
    db: Session,
    source_id,
    external_id,
    title,
    post_url
):
    existing_post = (
        db.query(Post)
        .filter(Post.external_id == external_id)
        .first()
    )

    if existing_post:
        return

    post = Post(
        source_id=source_id,
        external_id=external_id,
        title=title,
        post_url=post_url
    )

    db.add(post)
    db.commit()