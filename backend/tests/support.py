"""
Test support helpers.

DATABASE SAFETY
---------------
These tests NEVER touch the application database. They connect to a separate
database whose name is the configured database name with a "_test" suffix
(e.g. marketbeacon -> marketbeacon_test), creating it if it does not exist.

Only that test database is ever written to or truncated. If the test database
name would collide with the real one, the run aborts.
"""

import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base

# Import every model so metadata is complete before create_all().
from app.models import user as _user            # noqa: F401
from app.models import post as _post            # noqa: F401
from app.models import alert as _alert          # noqa: F401
from app.models import notification as _notif   # noqa: F401
from app.models import notification_summary as _ns  # noqa: F401
from app.models import watchlist as _watchlist  # noqa: F401
from app.models import holding as _holding      # noqa: F401
from app.models import chat as _chat            # noqa: F401
from app.models import research_document as _rd  # noqa: F401
from app.models import research_metric as _rm   # noqa: F401
from app.models import research_cache as _rc    # noqa: F401
from app.models import research_report as _rr   # noqa: F401
from app.models import research_workspace as _rw  # noqa: F401
from app.models import daily_briefing as _db_   # noqa: F401
from app.models import timeline_event as _te    # noqa: F401
from app.models import source as _src           # noqa: F401
from app.models import twitter_follow as _tf    # noqa: F401
from app.models import tweet_notification as _tn  # noqa: F401
from app.models import push_subscription as _ps  # noqa: F401

_engine = None
_Session = None


def _test_database_url():
    url = make_url(settings.DATABASE_URL)
    real_name = url.database
    test_name = f"{real_name}_test"
    if test_name == real_name:
        raise RuntimeError("Refusing to run: test database name equals the real database name.")
    return url.set(database=test_name), url.set(database="postgres"), test_name, real_name


def get_engine():
    """Creates (if needed) and returns an engine bound to the TEST database."""
    global _engine, _Session
    if _engine is not None:
        return _engine

    test_url, admin_url, test_name, real_name = _test_database_url()

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": test_name}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{test_name}"'))
    admin_engine.dispose()

    _engine = create_engine(test_url)
    # Guard: make sure we really are on the test database.
    with _engine.connect() as conn:
        current = conn.execute(text("SELECT current_database()")).scalar()
        assert current == test_name, f"Connected to {current}, expected {test_name}"
        assert current != real_name, "Refusing to run against the application database."

    Base.metadata.create_all(bind=_engine)
    _Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session():
    get_engine()
    return _Session()


def reset_tables(*tables):
    """Truncates only the named tables in the TEST database."""
    engine = get_engine()
    with engine.connect() as conn:
        with conn.begin():
            for t in tables:
                conn.execute(text(f'TRUNCATE TABLE {t} RESTART IDENTITY CASCADE'))


def make_user(db, email=None, role="user", full_name="Test User"):
    from app.models.user import User
    from app.services.auth_service import hash_password

    u = User(
        id=uuid.uuid4(),
        full_name=full_name,
        email=email or f"{uuid.uuid4().hex[:12]}@example.test",
        password_hash=hash_password("CorrectHorseBattery1!"),
        role=role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def make_post(db, title, importance_score=90, impact_level="CRITICAL", event_type="EARNINGS"):
    from app.models.post import Post

    p = Post(
        id=uuid.uuid4(),
        source_id="test_source",
        external_id=f"https://example.test/{uuid.uuid4().hex}",
        title=title,
        content="test content",
        post_url=f"https://example.test/{uuid.uuid4().hex}",
        event_type=event_type,
        importance_score=importance_score,
        impact_level=impact_level,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p
