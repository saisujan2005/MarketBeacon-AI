from app.db.database import SessionLocal

from app.models.post import Post
from app.models.source import Source

from app.agents.event_detector import detect_event

db = SessionLocal()

posts = db.query(Post).all()

for post in posts:

    post.event_type = detect_event(
        post.title or ""
    )

db.commit()

print(
    f"Updated {len(posts)} posts"
)