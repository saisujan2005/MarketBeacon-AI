"""
RSS feed fetching.

feedparser.parse(url) performs its own HTTP request with NO timeout, so a single
slow or unresponsive feed can hang the caller indefinitely. The ingestion
pipeline runs 23 feeds sequentially, so one bad host was able to stall the whole
run (and, previously, application startup).

We therefore fetch the bytes ourselves with an explicit connect/read timeout and
hand the payload to feedparser, which parses without touching the network.
"""

import logging

import feedparser
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

# Some publishers reject requests without a conventional User-Agent.
_USER_AGENT = "MarketBeaconAI/1.0 (+https://github.com/saisujan2005/MarketBeacon-AI)"


def fetch_rss_feed(feed_url: str, timeout: float | None = None):
    """
    Fetches and parses a feed. Returns a list of article dicts, or an empty list
    if the feed could not be retrieved or parsed.

    Never raises: the caller ingests many feeds in sequence and one bad feed must
    not abort the run. Failures are logged explicitly rather than swallowed.
    """
    timeout = timeout if timeout is not None else settings.RSS_FETCH_TIMEOUT_SECONDS

    try:
        response = requests.get(
            feed_url,
            timeout=timeout,                     # (connect + read) seconds
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
        payload = response.content
    except requests.exceptions.Timeout:
        logger.warning("[RSS] Timeout after %ss fetching feed: %s", timeout, feed_url)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("[RSS] Failed to fetch feed %s: %s", feed_url, e)
        return []

    try:
        feed = feedparser.parse(payload)
    except Exception as e:
        logger.warning("[RSS] Failed to parse feed %s: %s", feed_url, e)
        return []

    if getattr(feed, "bozo", False) and not feed.entries:
        logger.warning(
            "[RSS] Malformed feed with no entries: %s (%s)",
            feed_url, getattr(feed, "bozo_exception", "unknown error"),
        )
        return []

    articles = []
    for entry in feed.entries:
        articles.append({
            "external_id": entry.get("link"),
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": entry.get("published", ""),
            "published_parsed": entry.get("published_parsed"),
            "summary": entry.get("summary", entry.get("description", "")),
        })

    return articles
