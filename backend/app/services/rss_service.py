import feedparser


def fetch_rss_feed(feed_url: str):
    feed = feedparser.parse(feed_url)

    articles = []

    for entry in feed.entries:
        articles.append({
             "external_id": entry.get("link"),
             "title": entry.get("title"),
             "link": entry.get("link"),
             "published": entry.get("published", ""),
             "published_parsed": entry.get("published_parsed"),
             "summary": entry.get("summary", entry.get("description", ""))
        })

    return articles