from app.db.database import SessionLocal
from app.collectors.rss_collector import collect_rss_feed
from app.models.source import Source
from app.models.post import Post

db = SessionLocal()

count = collect_rss_feed(
    db=db,
    source_id="f41e08c8-ce00-40f3-b130-0a9109c753d1",
    feed_url="https://feeds.feedburner.com/ndtvprofit-latest"
)

print(f"Saved {count} posts")