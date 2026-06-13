from app.db.database import SessionLocal

from app.models.post import Post
from app.models.source import Source

from app.agents.importance_agent import score_event

db = SessionLocal()

posts = db.query(Post).all()

for post in posts:

    post.importance_score = score_event(
        post.event_type
    )

db.commit()

print(
    f"Updated {len(posts)} posts"
)