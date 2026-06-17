"""
Twitter collector using twscrape.

Install:
    pip install twscrape

First-time setup (run once):
    python -m app.collectors.twitter_collector --setup
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL")


async def _get_client():
    """
    Returns an authenticated twscrape API client.
    Accounts are cached in twscrape's local DB after first login.
    """
    from twscrape import API
    api = API()

    # Add account only if not already added
    await api.pool.add_account(
        username=TWITTER_USERNAME,
        password=TWITTER_PASSWORD,
        email=TWITTER_EMAIL,
        email_password=TWITTER_PASSWORD,  # use same or set separately
    )
    await api.pool.login_all()
    return api


async def fetch_latest_tweets(handle: str, since_tweet_id: str = None, limit: int = 5):
    """
    Fetch latest tweets from a handle.
    If since_tweet_id is provided, only return tweets newer than that.
    Returns list of dicts with tweet data.
    """
    from twscrape import API, gather
    from twscrape.models import Tweet

    try:
        api = await _get_client()
        tweets = []

        async for tweet in api.user_tweets(handle, limit=20):
            # Skip retweets — only original tweets matter for market signals
            if tweet.retweetedTweet:
                continue

            # Stop if we've seen this tweet before
            if since_tweet_id and str(tweet.id) <= since_tweet_id:
                break

            tweets.append({
                "tweet_id": str(tweet.id),
                "text": tweet.rawContent,
                "url": f"https://x.com/{handle}/status/{tweet.id}",
                "created_at": tweet.date,
            })

            if len(tweets) >= limit:
                break

        return tweets

    except Exception as e:
        logger.error(f"Failed to fetch tweets for @{handle}: {e}")
        return []


def fetch_latest_tweets_sync(handle: str, since_tweet_id: str = None, limit: int = 5):
    """Synchronous wrapper for use in non-async contexts (scheduler)."""
    return asyncio.run(
        fetch_latest_tweets(handle, since_tweet_id, limit)
    )


# ── First-time setup ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def setup():
        print("Setting up Twitter scraper account...")
        api = await _get_client()
        print("Login successful! Account added to twscrape pool.")
        print("\nTest fetch from @NSEIndia:")
        tweets = await fetch_latest_tweets("NSEIndia", limit=3)
        for t in tweets:
            print(f"  [{t['tweet_id']}] {t['text'][:80]}...")

    asyncio.run(setup())