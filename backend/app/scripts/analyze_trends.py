from app.db.database import SessionLocal

from app.models.post import Post
from app.models.source import Source

from app.agents.trend_agent import (
    detect_trends
)

db = SessionLocal()

posts = db.query(Post).all()

trends = detect_trends(
    posts
)

print("\nTREND REPORT\n")

for event, count in trends.items():

    print(
        f"{event}: {count}"
    )