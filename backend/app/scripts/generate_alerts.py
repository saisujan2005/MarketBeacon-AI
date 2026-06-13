from app.db.database import SessionLocal

from app.models.post import Post
from app.models.source import Source

from app.models.alert import Alert

from app.agents.alert_agent import should_alert


db = SessionLocal()

posts = db.query(Post).all()

count = 0

for post in posts:

    if not should_alert(
        post.importance_score
    ):
        continue

    existing = (
        db.query(Alert)
        .filter(Alert.title == post.title)
        .first()
    )

    if existing:
        continue

    alert = Alert(
        title=post.title,
        event_type=post.event_type,
        importance_score=str(
            post.importance_score
        )
    )

    db.add(alert)

    count += 1

db.commit()

print(
    f"Created {count} alerts"
)