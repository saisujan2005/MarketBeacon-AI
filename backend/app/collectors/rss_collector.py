from sqlalchemy.orm import Session

from app.models.post import Post
from app.services.rss_service import fetch_rss_feed
from app.agents.event_detector import detect_event


def collect_rss_feed(
    db: Session,
    source_id,
    feed_url
):

    articles = fetch_rss_feed(feed_url)

    saved_count = 0

    for article in articles:

        existing_post = (
            db.query(Post)
            .filter(
                Post.external_id ==
                article["link"]
            )
            .first()
        )

        if existing_post:
            continue

        event_type = detect_event(
            article["title"]
        )

        post = Post(
            source_id=source_id,
            external_id=article["link"],
            title=article["title"],
            post_url=article["link"],
            event_type=event_type
        )

        db.add(post)

        saved_count += 1

    db.commit()

    return saved_count