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

    # ── Indian News Outlets ───────────────────────────────────────────────────
    {
        "source_id": "ndtv_profit",
        "feed_url": "https://feeds.feedburner.com/ndtvprofit-latest",
    },
    {
        "source_id": "economic_times_markets",
        "feed_url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    },
    {
        "source_id": "moneycontrol",
        "feed_url": "https://www.moneycontrol.com/rss/latestnews.xml",
    },
    {
        "source_id": "livemint_markets",
        "feed_url": "https://www.livemint.com/rss/markets",
    },
    {
        "source_id": "financial_express_markets",
        "feed_url": "https://www.financialexpress.com/market/feed/",
    },
    {
        "source_id": "business_standard_markets",
        "feed_url": "https://www.business-standard.com/rss/markets-106.rss",
    },

    # ── Indian Regulatory & Official ──────────────────────────────────────────
    {
        "source_id": "rbi",
        "feed_url": "https://www.rbi.org.in/scripts/rss.aspx",
    },
    {
        "source_id": "sebi",
        "feed_url": "https://www.sebi.gov.in/sebi_data/rss/rss.xml",
    },
    {
        "source_id": "pib_finance",
        "feed_url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
    },
    {
        "source_id": "bse_india",
        "feed_url": "https://www.bseindia.com/xml-data/corpfiling/AttachHis/rss.xml",
    },

    # ── Global News Outlets ───────────────────────────────────────────────────
    {
        "source_id": "reuters_business",
        "feed_url": "https://feeds.reuters.com/reuters/businessNews",
    },
    {
        "source_id": "reuters_markets",
        "feed_url": "https://feeds.reuters.com/reuters/marketsNews",
    },
    {
        "source_id": "bloomberg_markets",
        "feed_url": "https://feeds.bloomberg.com/markets/news.rss",
    },
    {
        "source_id": "ft_markets",
        "feed_url": "https://www.ft.com/markets?format=rss",
    },

    # ── Wall Street & US Official ─────────────────────────────────────────────
    {
        "source_id": "federal_reserve",
        "feed_url": "https://www.federalreserve.gov/feeds/press_all.xml",
    },
    {
        "source_id": "sec_press",
        "feed_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&dateb=&owner=include&count=10&search_text=&output=atom",
    },
    {
        "source_id": "cnbc_markets",
        "feed_url": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    },
    {
        "source_id": "wsj_markets",
        "feed_url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    },
    {
        "source_id": "marketwatch",
        "feed_url": "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    },

    # ── Crypto ────────────────────────────────────────────────────────────────
    {
        "source_id": "coindesk",
        "feed_url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    },
    {
        "source_id": "cointelegraph",
        "feed_url": "https://cointelegraph.com/rss",
    },
]


def run_ingestion_pipeline():
    logger.info("--- Ingestion pipeline starting ---")
    total_saved = 0

    # Step 1: collect — isolated session per feed
    for feed in RSS_FEEDS:
        db = SessionLocal()
        try:
            saved = collect_rss_feed(
                db=db,
                source_id=feed["source_id"],
                feed_url=feed["feed_url"]
            )
            logger.info(f"  {feed['source_id']}: {saved} new articles")
            total_saved += saved
        except Exception as e:
            logger.error(f"  {feed['source_id']} failed: {e}")
            db.rollback()
        finally:
            db.close()

    logger.info(f"Total new articles: {total_saved}")

    # Step 2: score
    db = SessionLocal()
    try:
        scored = score_posts(db)
        logger.info(f"Posts scored: {scored}")
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        db.rollback()
    finally:
        db.close()

    # Step 3: alerts
    db = SessionLocal()
    try:
        count = generate_alerts(db)
        logger.info(f"Alerts generated: {count}")
    except Exception as e:
        logger.error(f"Alert generation failed: {e}")
        db.rollback()
    finally:
        db.close()

    # Step 4: notifications
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

    # Run immediately on startup
    run_ingestion_pipeline()

    return scheduler