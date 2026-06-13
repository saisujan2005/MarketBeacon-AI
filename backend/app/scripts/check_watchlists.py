from app.db.database import SessionLocal

from app.models.watchlist import Watchlist
from app.models.alert import Alert

from app.agents.watchlist_agent import (
    match_watchlist
)

db = SessionLocal()

watchlists = db.query(
    Watchlist
).all()

alerts = db.query(
    Alert
).all()

keywords = [
    w.keyword
    for w in watchlists
]

print("\nWATCHLIST MATCHES\n")

for alert in alerts:

    matches = match_watchlist(
        alert.title,
        keywords
    )

    if matches:

        print(
            f"ALERT: {alert.title}"
        )

        print(
            f"MATCHES: {matches}"
        )

        print("-" * 50)