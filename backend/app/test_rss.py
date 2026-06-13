from app.services.rss_service import fetch_rss_feed

feed_url = "https://feeds.feedburner.com/ndtvprofit-latest"

articles = fetch_rss_feed(feed_url)

print("Number of articles:", len(articles))

print("\nFirst article:")
print(articles[0])