from app.services.rss_service import fetch_rss_feed
from app.collectors.article_extractor import extract_article

feed_url = "https://feeds.feedburner.com/ndtvprofit-latest"

articles = fetch_rss_feed(feed_url)

url = articles[0]["link"]

print("URL:", url)

content = extract_article(url)

print("Length:", len(content))
print(content[:1000])