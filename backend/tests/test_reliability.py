"""
Reliability regression tests.

(a) FastAPI startup is not blocked by RSS ingestion.
(b) Slow / failing / malformed RSS feeds are handled without hanging.
(c) Two different users can cache and watch the same company.
(d) Existing single-user cache behaviour is preserved.
"""

import inspect as _inspect
import threading
import time
import uuid

import requests
from sqlalchemy import text

from app.core.config import settings
from app.models.research_cache import CompanyPeerCache
from app.services import rss_service
from app.scheduler import news_scheduler
from tests.support import get_engine, get_session, make_user, reset_tables


# ── (a) startup is not blocked by ingestion ──────────────────────────────────

def test_start_scheduler_does_not_run_ingestion_inline():
    """
    start_scheduler() must return promptly. Previously it called
    run_ingestion_pipeline() synchronously, so the FastAPI lifespan (and every
    health check) waited for all 23 feeds to be fetched and scored.
    """
    source = _inspect.getsource(news_scheduler.start_scheduler)

    # Look for an actual statement-level call, ignoring the docstring/comments
    # (which legitimately mention run_ingestion_pipeline() when explaining the fix).
    offending = [
        line for line in source.splitlines()
        if line.strip() == "run_ingestion_pipeline()"
    ]
    assert not offending, (
        "start_scheduler must not execute the ingestion pipeline inline; "
        f"found: {offending}"
    )
    assert "next_run_time" in source, (
        "The first ingestion pass should be scheduled, not called directly."
    )


def test_start_scheduler_returns_immediately_even_if_ingestion_is_slow(monkeypatch=None):
    """Replace the pipeline with a slow function; startup must still be fast."""
    original = news_scheduler.run_ingestion_pipeline
    started = threading.Event()

    def slow_pipeline():
        started.set()
        time.sleep(5)

    news_scheduler.run_ingestion_pipeline = slow_pipeline
    scheduler = None
    try:
        t0 = time.time()
        scheduler = news_scheduler.start_scheduler(interval_minutes=10)
        elapsed = time.time() - t0

        assert elapsed < 2.0, (
            f"start_scheduler blocked for {elapsed:.2f}s; it must return immediately."
        )
        # The run really was queued, just not inline.
        assert started.wait(timeout=10), "The first ingestion pass was never scheduled."
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)
        news_scheduler.run_ingestion_pipeline = original


def test_ingestion_job_is_configured_against_overlapping_runs():
    source = _inspect.getsource(news_scheduler.start_scheduler)
    assert "max_instances=1" in source
    assert "coalesce=True" in source


def test_scheduler_startup_failure_does_not_abort_app_startup():
    from app import main
    source = _inspect.getsource(main.lifespan)
    assert "news_scheduler = None" in source
    assert "Failed to start the news scheduler" in source, (
        "Scheduler startup must be guarded so the API still comes up."
    )


# ── (b) slow / failing RSS feeds ─────────────────────────────────────────────

def test_rss_fetch_has_a_configured_timeout():
    assert settings.RSS_FETCH_TIMEOUT_SECONDS > 0
    source = _inspect.getsource(rss_service.fetch_rss_feed)
    assert "timeout=timeout" in source, "The HTTP fetch must pass an explicit timeout."
    assert "feedparser.parse(payload)" in source, (
        "feedparser must parse bytes, not perform its own untimed network call."
    )


def _patch_requests_get(fn):
    original = requests.get
    requests.get = fn
    return original


def test_timeout_returns_empty_list_and_does_not_raise():
    original = _patch_requests_get(
        lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.Timeout("timed out"))
    )
    try:
        assert rss_service.fetch_rss_feed("http://slow.example/feed") == []
    finally:
        requests.get = original


def test_connection_error_returns_empty_list():
    original = _patch_requests_get(
        lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.ConnectionError("refused"))
    )
    try:
        assert rss_service.fetch_rss_feed("http://down.example/feed") == []
    finally:
        requests.get = original


def test_http_error_status_returns_empty_list():
    class Resp:
        content = b""
        def raise_for_status(self):
            raise requests.exceptions.HTTPError("503")

    original = _patch_requests_get(lambda *a, **k: Resp())
    try:
        assert rss_service.fetch_rss_feed("http://err.example/feed") == []
    finally:
        requests.get = original


def test_malformed_feed_returns_empty_list():
    class Resp:
        content = b"<<<not xml at all>>>"
        def raise_for_status(self):
            return None

    original = _patch_requests_get(lambda *a, **k: Resp())
    try:
        assert rss_service.fetch_rss_feed("http://junk.example/feed") == []
    finally:
        requests.get = original


def test_valid_feed_is_parsed_normally():
    rss = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel><title>T</title>
      <item><title>RBI cuts repo rate</title><link>https://example.test/a1</link>
            <description>Body</description></item>
      <item><title>Fed holds steady</title><link>https://example.test/a2</link>
            <description>Body 2</description></item>
    </channel></rss>"""

    class Resp:
        content = rss
        def raise_for_status(self):
            return None

    original = _patch_requests_get(lambda *a, **k: Resp())
    try:
        articles = rss_service.fetch_rss_feed("http://ok.example/feed")
        assert len(articles) == 2
        assert articles[0]["title"] == "RBI cuts repo rate"
        assert articles[0]["link"] == "https://example.test/a1"
        assert "summary" in articles[0]
    finally:
        requests.get = original


def test_one_bad_feed_does_not_stop_the_others():
    """The pipeline iterates many feeds; a single failure must not abort the run."""
    calls = {"n": 0}

    def flaky(url, *a, **k):
        calls["n"] += 1
        if "bad" in url:
            raise requests.exceptions.Timeout("timed out")
        class Resp:
            content = (b'<?xml version="1.0"?><rss version="2.0"><channel>'
                       b'<item><title>OK</title><link>https://example.test/ok</link></item>'
                       b'</channel></rss>')
            def raise_for_status(self): return None
        return Resp()

    original = _patch_requests_get(flaky)
    try:
        results = [rss_service.fetch_rss_feed(u) for u in
                   ["http://bad.example/f", "http://good.example/f", "http://bad.example/g"]]
        assert results[0] == []
        assert len(results[1]) == 1
        assert results[2] == []
        assert calls["n"] == 3, "Every feed should still be attempted."
    finally:
        requests.get = original


# ── (c) + (d) peer cache is per-user ─────────────────────────────────────────

def test_peer_cache_company_name_index_is_not_unique():
    """
    A globally-unique index on company_name made the cache single-tenant.
    Uniqueness must be (user_id, company_name) only.
    """
    engine = get_engine()
    with engine.connect() as c:
        is_unique = c.execute(text("""
            SELECT i.indisunique FROM pg_class cl
              JOIN pg_index i ON i.indexrelid = cl.oid
             WHERE cl.relname = 'ix_company_peer_caches_company_name'
        """)).scalar()
        if is_unique is not None:
            assert is_unique is False, (
                "ix_company_peer_caches_company_name must NOT be unique."
            )

        composite = c.execute(text("""
            SELECT 1 FROM pg_constraint con JOIN pg_class rel ON rel.oid = con.conrelid
             WHERE rel.relname = 'company_peer_caches' AND con.conname = 'uq_user_company_peer'
        """)).scalar()
        assert composite == 1, "uq_user_company_peer (user_id, company_name) must exist."


def test_two_users_can_cache_the_same_company():
    """User A caching HDFC Bank must not block User B from doing the same."""
    reset_tables("company_peer_caches", "users")
    db = get_session()
    try:
        user_a = make_user(db, email="peer-a@example.test")
        user_b = make_user(db, email="peer-b@example.test")

        db.add(CompanyPeerCache(
            id=uuid.uuid4(), user_id=user_a.id, company_name="HDFC Bank",
            sector="Financials", industry="Banking", peers=["ICICI Bank"],
        ))
        db.commit()

        # This is the insert that previously raised UniqueViolation.
        db.add(CompanyPeerCache(
            id=uuid.uuid4(), user_id=user_b.id, company_name="HDFC Bank",
            sector="Financials", industry="Banking", peers=["Axis Bank"],
        ))
        db.commit()

        assert db.query(CompanyPeerCache).filter(
            CompanyPeerCache.company_name == "HDFC Bank").count() == 2
        a_row = db.query(CompanyPeerCache).filter(CompanyPeerCache.user_id == user_a.id).one()
        b_row = db.query(CompanyPeerCache).filter(CompanyPeerCache.user_id == user_b.id).one()
        assert a_row.peers == ["ICICI Bank"]
        assert b_row.peers == ["Axis Bank"], "Each user must keep their own cached peers."
    finally:
        db.close()


def test_same_user_cannot_duplicate_a_company():
    """Existing behaviour preserved: one cache row per (user, company)."""
    reset_tables("company_peer_caches", "users")
    db = get_session()
    try:
        user = make_user(db, email="peer-dup@example.test")
        db.add(CompanyPeerCache(
            id=uuid.uuid4(), user_id=user.id, company_name="TCS", peers=["Infosys"],
        ))
        db.commit()

        db.add(CompanyPeerCache(
            id=uuid.uuid4(), user_id=user.id, company_name="TCS", peers=["Wipro"],
        ))
        violated = False
        try:
            db.commit()
        except Exception:
            violated = True
            db.rollback()

        assert violated, "(user_id, company_name) must still be unique for one user."
        assert db.query(CompanyPeerCache).filter(CompanyPeerCache.user_id == user.id).count() == 1
    finally:
        db.close()


def test_existing_cache_lookup_still_works_per_user():
    """discover_company_peers reads back the caller's own cached entry."""
    reset_tables("company_peer_caches", "users")
    db = get_session()
    try:
        from app.services.research_agent import discover_company_peers

        user_a = make_user(db, email="peer-read-a@example.test")
        user_b = make_user(db, email="peer-read-b@example.test")

        db.add(CompanyPeerCache(
            id=uuid.uuid4(), user_id=user_a.id, company_name="Nvidia",
            sector="Technology", industry="Semiconductors", peers=["AMD", "Intel"],
        ))
        db.commit()

        got = discover_company_peers(db, "Nvidia", user_a.id)
        assert got["peers"] == ["AMD", "Intel"], "User A must get their cached peers."
        assert got["sector"] == "Technology"

        # User B has no cache entry, so A's row must not be returned to them.
        b_cached = db.query(CompanyPeerCache).filter(
            CompanyPeerCache.user_id == user_b.id,
            CompanyPeerCache.company_name.ilike("Nvidia"),
        ).first()
        assert b_cached is None
    finally:
        db.close()
