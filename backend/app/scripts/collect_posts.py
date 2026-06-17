"""
Manual collection script — runs the full ingestion pipeline once.

Run from backend/ directory:
    python -m app.scripts.collect_posts
"""

import logging
from app.db.database import SessionLocal
from app.collectors.rss_collector import collect_rss_feed
from app.scripts.score_posts import score_posts
from app.scripts.generate_alerts import generate_alerts
from app.scripts.generate_notifications import generate_notifications

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger(__name__)

RSS_FEEDS = [

    # ── Direct news feeds — mixed topics, up to 15 articles ──────────────────
    {"source_id": "ndtv_profit",             "feed_url": "https://feeds.feedburner.com/ndtvprofit-latest",                                                                    "max": 15},
    {"source_id": "economic_times_markets",  "feed_url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",                                              "max": 15},
    {"source_id": "livemint_markets",        "feed_url": "https://www.livemint.com/rss/markets",                                                                              "max": 15},
    {"source_id": "livemint_economy",        "feed_url": "https://www.livemint.com/rss/economy",                                                                              "max": 10},
    {"source_id": "hindu_business",          "feed_url": "https://www.thehindubusinessline.com/markets/feeder/default.rss",                                                   "max": 15},
    {"source_id": "bloomberg_markets",       "feed_url": "https://feeds.bloomberg.com/markets/news.rss",                                                                      "max": 15},
    {"source_id": "ft_markets",              "feed_url": "https://www.ft.com/markets?format=rss",                                                                             "max": 10},
    {"source_id": "federal_reserve",         "feed_url": "https://www.federalreserve.gov/feeds/press_all.xml",                                                                "max": 10},
    {"source_id": "cnbc_markets",            "feed_url": "https://www.cnbc.com/id/20910258/device/rss/rss.html",                                                              "max": 15},
    {"source_id": "wsj_markets",             "feed_url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",                                                                    "max": 15},
    {"source_id": "marketwatch",             "feed_url": "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",                                                      "max": 15},
    {"source_id": "coindesk",                "feed_url": "https://www.coindesk.com/arc/outboundfeeds/rss/",                                                                   "max": 10},
    {"source_id": "cointelegraph",           "feed_url": "https://cointelegraph.com/rss",                                                                                     "max": 10},

    # ── Google News — topic-locked, limit to 5 to avoid flooding ─────────────
    {"source_id": "gnews_indian_markets",    "feed_url": "https://news.google.com/rss/search?q=NSE+BSE+nifty+sensex&hl=en-IN&gl=IN&ceid=IN:en",                             "max": 5},
    {"source_id": "gnews_rbi",               "feed_url": "https://news.google.com/rss/search?q=RBI+reserve+bank+india&hl=en-IN&gl=IN&ceid=IN:en",                           "max": 5},
    {"source_id": "gnews_sebi",              "feed_url": "https://news.google.com/rss/search?q=SEBI+regulation+india&hl=en-IN&gl=IN&ceid=IN:en",                            "max": 5},
    {"source_id": "gnews_fed",               "feed_url": "https://news.google.com/rss/search?q=federal+reserve+interest+rate&hl=en-US&gl=US&ceid=US:en",                    "max": 5},
    {"source_id": "gnews_wallstreet",        "feed_url": "https://news.google.com/rss/search?q=wall+street+stock+market&hl=en-US&gl=US&ceid=US:en",                         "max": 5},
    {"source_id": "gnews_crypto",            "feed_url": "https://news.google.com/rss/search?q=bitcoin+crypto+market&hl=en-US&gl=US&ceid=US:en",                            "max": 5},
    {"source_id": "gnews_commodities",       "feed_url": "https://news.google.com/rss/search?q=gold+oil+commodity+market&hl=en-US&gl=US&ceid=US:en",                        "max": 5},
    {"source_id": "gnews_ipo",               "feed_url": "https://news.google.com/rss/search?q=IPO+india+stock+listing&hl=en-IN&gl=IN&ceid=IN:en",                          "max": 5},
    {"source_id": "gnews_earnings",          "feed_url": "https://news.google.com/rss/search?q=quarterly+earnings+results+profit&hl=en-US&gl=US&ceid=US:en",                "max": 5},
]


def main():
    total_articles = 0

    for feed in RSS_FEEDS:
        logger.info(f"Fetching {feed['source_id']}...")
        db = SessionLocal()
        try:
            saved = collect_rss_feed(
                db=db,
                source_id=feed["source_id"],
                feed_url=feed["feed_url"],
                max_per_feed=feed["max"]
            )
            logger.info(f"  -> {saved} new articles")
            total_articles += saved
        except Exception as e:
            logger.error(f"  -> Failed: {e}")
            db.rollback()
        finally:
            db.close()

    logger.info(f"Total new articles: {total_articles}")

    db = SessionLocal()
    try:
        logger.info("Scoring posts...")
        scored = score_posts(db)
        logger.info(f"  -> {scored} posts scored")
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        db.rollback()
    finally:
        db.close()

    db = SessionLocal()
    try:
        logger.info("Generating alerts...")
        alerts = generate_alerts(db)
        logger.info(f"  -> {alerts} new alerts")
    except Exception as e:
        logger.error(f"Alert generation failed: {e}")
        db.rollback()
    finally:
        db.close()

    db = SessionLocal()
    try:
        logger.info("Generating notifications...")
        notifs = generate_notifications(db)
        logger.info(f"  -> {notifs} new notifications")
    except Exception as e:
        logger.error(f"Notification generation failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()