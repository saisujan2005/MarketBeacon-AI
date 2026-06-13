from app.db.database import SessionLocal

from app.models.alert import Alert
from app.models.watchlist import Watchlist
from app.models.notification import Notification

from app.agents.watchlist_agent import match_watchlist

db = SessionLocal()

alerts = db.query(Alert).all()

watchlists = db.query(
    Watchlist
).all()

keywords = [
    w.keyword
    for w in watchlists
]

created = 0

for alert in alerts:

    matches = match_watchlist(
        alert.title,
        keywords
    )

    for keyword in matches:

        existing = (
            db.query(Notification)
            .filter(
                Notification.keyword == keyword,
                Notification.title == alert.title
            )
            .first()
        )

        if existing:
            continue

        notification = Notification(
            keyword=keyword,
            title=alert.title
        )

        db.add(notification)

        created += 1

db.commit()

print(
    f"Created {created} notifications"
)