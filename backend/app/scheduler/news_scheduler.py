import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.database import SessionLocal
from app.collectors.rss_collector import collect_rss_feed
from app.scripts.score_posts import score_posts
from app.scripts.generate_alerts import generate_alerts
from app.scripts.generate_notifications import generate_notifications

logger = logging.getLogger(__name__)

RSS_FEEDS = [

    # ── Direct news feeds — mixed topics ─────────────────────────────────────
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

    # ── Google News — topic-locked, limit to 5 ───────────────────────────────
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


def run_ingestion_pipeline():
    logger.info("--- Ingestion pipeline starting ---")
    total_saved = 0

    for feed in RSS_FEEDS:
        db = SessionLocal()
        try:
            saved = collect_rss_feed(
                db=db,
                source_id=feed["source_id"],
                feed_url=feed["feed_url"],
                max_per_feed=feed["max"]
            )
            logger.info(f"  {feed['source_id']}: {saved} new articles")
            total_saved += saved
        except Exception as e:
            logger.error(f"  {feed['source_id']} failed: {e}")
            db.rollback()
        finally:
            db.close()

    logger.info(f"Total new articles: {total_saved}")

    db = SessionLocal()
    try:
        scored = score_posts(db)
        logger.info(f"Posts scored: {scored}")
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        db.rollback()
    finally:
        db.close()

    db = SessionLocal()
    try:
        count = generate_alerts(db)
        logger.info(f"Alerts generated: {count}")
    except Exception as e:
        logger.error(f"Alert generation failed: {e}")
        db.rollback()
    finally:
        db.close()

    db = SessionLocal()
    try:
        count = generate_notifications(db)
        logger.info(f"Notifications generated: {count}")
    except Exception as e:
        logger.error(f"Notification generation failed: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("--- Ingestion pipeline complete ---\n")


def start_scheduler(interval_minutes: int = 10):
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        func=run_ingestion_pipeline,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="news_ingestion",
        name="Collect news + score + alerts + notifications",
        replace_existing=True,
        misfire_grace_time=60,
    )

    scheduler.start()
    logger.info(f"Scheduler started - running every {interval_minutes} minutes")
    run_ingestion_pipeline()
    return scheduler