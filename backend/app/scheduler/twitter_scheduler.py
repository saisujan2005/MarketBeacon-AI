"""
Twitter monitoring scheduler.

Polls followed handles:
  - Every 2 minutes during market hours (9am-4pm IST)
  - Every 15 minutes outside market hours
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.twitter_follow import TwitterFollow
from app.models.tweet_notification import TweetNotification
from app.collectors.twitter_collector import fetch_latest_tweets_sync
from app.agents.event_detector import detect_event
from app.agents.importance_agent import score_event

load_dotenv()
logger = logging.getLogger(__name__)

MARKET_OPEN_HOUR  = int(os.getenv("MARKET_OPEN_HOUR", 9))
MARKET_CLOSE_HOUR = int(os.getenv("MARKET_CLOSE_HOUR", 16))
MARKET_INTERVAL   = int(os.getenv("TWITTER_MARKET_HOURS_INTERVAL", 2))
OFF_INTERVAL      = int(os.getenv("TWITTER_OFF_HOURS_INTERVAL", 15))

IST = timezone(timedelta(hours=5, minutes=30))


def is_market_hours() -> bool:
    now_ist = datetime.now(IST)
    return (
        now_ist.weekday() < 5 and  # Monday–Friday
        MARKET_OPEN_HOUR <= now_ist.hour < MARKET_CLOSE_HOUR
    )


def generate_tweet_summary(handle: str, tweet_text: str, event_type: str) -> str:
    """
    Use Ollama/LLM to generate a short market-impact summary for the tweet.
    Falls back to a simple template if LLM is unavailable.
    """
    try:
        from app.rag.llm_service import ask_llm

        prompt = (
            f"@{handle} just tweeted:\n\"{tweet_text}\"\n\n"
            f"This has been classified as a {event_type} event.\n"
            f"In 1-2 sentences, explain why this tweet could impact financial markets. "
            f"Be direct and concise. No preamble."
        )
        return ask_llm(prompt)

    except Exception as e:
        logger.warning(f"LLM summary failed, using fallback: {e}")
        return (
            f"@{handle} tweeted about {event_type.lower().replace('_', ' ')}. "
            f"Monitor for market impact."
        )


def process_handle(db: Session, follow: TwitterFollow):
    """
    Fetch new tweets for a single handle and create notifications.
    """
    logger.info(f"Checking @{follow.handle}...")

    tweets = fetch_latest_tweets_sync(
        handle=follow.handle,
        since_tweet_id=follow.last_tweet_id,
        limit=5
    )

    if not tweets:
        logger.info(f"  No new tweets for @{follow.handle}")
        return

    new_notifications = 0

    for tweet in tweets:
        # Skip if already processed
        existing = (
            db.query(TweetNotification)
            .filter(TweetNotification.tweet_id == tweet["tweet_id"])
            .first()
        )
        if existing:
            continue

        # Classify and score
        event_type = detect_event(tweet["text"])
        importance = score_event(event_type)

        # Only notify if score >= 70 (skip pure OTHER/noise)
        if importance < 70:
            logger.info(
                f"  Skipping low-importance tweet "
                f"(score={importance}, type={event_type})"
            )
            continue

        # Generate LLM summary
        summary = generate_tweet_summary(
            follow.handle, tweet["text"], event_type
        )

        notification = TweetNotification(
            handle=follow.handle,
            label=follow.label or f"@{follow.handle}",
            tweet_id=tweet["tweet_id"],
            tweet_text=tweet["text"],
            tweet_url=tweet["url"],
            event_type=event_type,
            importance_score=importance,
            summary=summary,
        )
        db.add(notification)
        new_notifications += 1

        logger.info(
            f"  New tweet alert: @{follow.handle} "
            f"[{event_type} / score={importance}]"
        )

    # Update last seen tweet id
    if tweets:
        follow.last_tweet_id = tweets[0]["tweet_id"]

    db.commit()
    logger.info(
        f"  @{follow.handle}: {new_notifications} new notifications"
    )


def run_twitter_monitor():
    """Poll all active followed handles for new tweets."""
    logger.info("--- Twitter monitor running ---")

    db = SessionLocal()
    try:
        follows = (
            db.query(TwitterFollow)
            .filter(TwitterFollow.is_active == True)  # noqa: E712
            .all()
        )

        if not follows:
            logger.info("No handles being followed yet.")
            return

        for follow in follows:
            try:
                process_handle(db, follow)
            except Exception as e:
                logger.error(f"Error processing @{follow.handle}: {e}")
                db.rollback()

    finally:
        db.close()

    logger.info("--- Twitter monitor complete ---\n")


def start_twitter_scheduler():
    """
    Start the Twitter monitoring scheduler.
    Dynamically adjusts interval based on market hours.
    """
    scheduler = BackgroundScheduler()

    # Use market-hours interval; APScheduler will reschedule
    # dynamically each time the job runs
    def smart_poll():
        interval = MARKET_INTERVAL if is_market_hours() else OFF_INTERVAL
        logger.info(
            f"Twitter poll — "
            f"{'market hours' if is_market_hours() else 'off hours'} "
            f"(next in {interval} min)"
        )
        run_twitter_monitor()

        # Reschedule with correct interval for current time
        scheduler.reschedule_job(
            "twitter_monitor",
            trigger=IntervalTrigger(minutes=interval)
        )

    initial_interval = MARKET_INTERVAL if is_market_hours() else OFF_INTERVAL

    scheduler.add_job(
        func=smart_poll,
        trigger=IntervalTrigger(minutes=initial_interval),
        id="twitter_monitor",
        name="Twitter handle monitor",
        replace_existing=True,
        misfire_grace_time=30,
    )

    scheduler.start()
    logger.info(
        f"Twitter scheduler started "
        f"(current interval: {initial_interval} min)"
    )
    return scheduler