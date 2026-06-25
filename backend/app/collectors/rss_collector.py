import re
from sqlalchemy.orm import Session

from app.models.post import Post
from app.services.rss_service import fetch_rss_feed
from app.agents.event_detector import detect_event

# Max new articles to save per feed per run
# Prevents topic-specific Google News feeds from flooding the DB
MAX_PER_FEED = 15


def normalize_title(title: str) -> str:
    """
    Normalize a title for deduplication.
    'RBI cuts rate! (Reuters)' and 'RBI cuts rate - Moneycontrol'
    both become 'rbi cuts rate'
    """
    if not title:
        return ""
    title = title.lower()
    # Remove source suffixes like "- Reuters", "| Moneycontrol"
    title = re.sub(r'[\|\-\–]\s*\w[\w\s]*$', '', title)
    # Remove punctuation
    title = re.sub(r'[^\w\s]', '', title)
    # Collapse whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def collect_rss_feed(
    db: Session,
    source_id: str,
    feed_url: str,
    max_per_feed: int = MAX_PER_FEED
) -> int:

    articles = fetch_rss_feed(feed_url)
    saved_count = 0

    for article in articles:

        # Stop once we hit the per-feed limit
        if saved_count >= max_per_feed:
            break

        title = article.get("title", "")
        link = article.get("link", "")

        if not title or not link:
            continue

        # 1. Deduplicate by URL
        existing_by_url = (
            db.query(Post)
            .filter(Post.external_id == link)
            .first()
        )
        if existing_by_url:
            continue

        # 2. Deduplicate by normalized title
        norm = normalize_title(title)
        if norm:
            existing_by_title = (
                db.query(Post)
                .filter(Post.title.ilike(f"%{norm[:60]}%"))
                .first()
            )
            if existing_by_title:
                continue

        published_parsed = article.get("published_parsed")
        posted_at = None
        if published_parsed:
            try:
                from datetime import datetime
                posted_at = datetime(*published_parsed[:6])
            except Exception:
                pass

        event_type = detect_event(title)

        post = Post(
            source_id=source_id,
            external_id=link,
            title=title,
            content=article.get("summary", ""),
            post_url=link,
            event_type=event_type,
            posted_at=posted_at
        )

        db.add(post)
        saved_count += 1

    db.commit()
    return saved_count