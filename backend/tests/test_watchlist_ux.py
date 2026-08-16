"""
Watchlist API behaviour backing the signup -> watchlist UX.

Covers the signup continuity chain (onboarding add -> DB -> list endpoint),
the suggestion list used by the first-run panel, and per-user scoping.
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db as db_get_db
from app.db.dependencies import get_db as dep_get_db, get_current_user
from app.models.watchlist import Watchlist
from tests.support import get_session, make_user, reset_tables


def _client_for(user, db):
    app.dependency_overrides[db_get_db] = lambda: db
    app.dependency_overrides[dep_get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _clear():
    app.dependency_overrides.clear()


def test_empty_search_returns_known_companies():
    """The first-run panel sources its chips here; it must not be empty."""
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user = make_user(db)
        client = _client_for(user, db)

        resp = client.get("/api/watchlist/search", params={"q": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0, "Empty query must return the known-company list"
        assert all("name" in c and "exchange" in c for c in data)
        names = [c["name"] for c in data]
        assert len(names) == len(set(names)), "Suggestions must be de-duplicated"
    finally:
        _clear()
        db.close()


def test_search_still_filters_on_a_query():
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user = make_user(db)
        client = _client_for(user, db)

        resp = client.get("/api/watchlist/search", params={"q": "tcs"})
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "TCS" in names
        assert len(names) < 8, "A specific query must narrow the results"
    finally:
        _clear()
        db.close()


def test_add_without_analysis_is_persisted():
    """
    Signup continuity: onboarding posts analyze=false. The row must still be
    created and returned by the list endpoint that the watchlist page uses.
    """
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user = make_user(db)
        client = _client_for(user, db)

        resp = client.post("/api/watchlist/add", json={"keyword": "Nvidia", "analyze": False})
        assert resp.status_code == 200, resp.text

        listed = client.get("/api/watchlist")
        assert listed.status_code == 200
        rows = listed.json()
        assert len(rows) == 1
        assert rows[0]["company_name"] == "Nvidia"
        # No analysis was requested, so the card renders its "pending" state.
        assert rows[0]["analysis_cache"] is None
    finally:
        _clear()
        db.close()


def test_signup_style_multi_add_keeps_every_company():
    """A brand-new user typing several companies must end up with all of them."""
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user = make_user(db)
        client = _client_for(user, db)

        typed = ["Nvidia", "Tesla", "Infosys"]
        for name in typed:
            r = client.post("/api/watchlist/add", json={"keyword": name, "analyze": False})
            assert r.status_code == 200, f"{name}: {r.text}"

        rows = client.get("/api/watchlist").json()
        assert len(rows) == len(typed), f"Expected {len(typed)} tracked companies, got {len(rows)}"
    finally:
        _clear()
        db.close()


def test_unknown_company_can_still_be_tracked():
    """
    The autocomplete only resolves a handful of names; the UI offers
    'Track "<query>"' for anything else. That path must work.
    """
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user = make_user(db)
        client = _client_for(user, db)

        r = client.post("/api/watchlist/add", json={"keyword": "Some Unlisted Co", "analyze": False})
        assert r.status_code == 200, r.text
        rows = client.get("/api/watchlist").json()
        assert len(rows) == 1
        assert rows[0]["company_name"]
    finally:
        _clear()
        db.close()


def test_duplicate_add_does_not_create_a_second_row():
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user = make_user(db)
        client = _client_for(user, db)

        client.post("/api/watchlist/add", json={"keyword": "Tesla", "analyze": False})
        client.post("/api/watchlist/add", json={"keyword": "Tesla", "analyze": False})

        rows = client.get("/api/watchlist").json()
        assert len(rows) == 1, f"Duplicate add created {len(rows)} rows"
    finally:
        _clear()
        db.close()


def test_remove_watchlist_item():
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user = make_user(db)
        client = _client_for(user, db)

        client.post("/api/watchlist/add", json={"keyword": "Tesla", "analyze": False})
        rows = client.get("/api/watchlist").json()
        assert len(rows) == 1

        d = client.delete(f"/api/watchlist/{rows[0]['id']}")
        assert d.status_code == 200
        assert client.get("/api/watchlist").json() == []
    finally:
        _clear()
        db.close()


def test_empty_watchlist_returns_empty_list_not_an_error():
    """The page must render a first-run state, not an error toast."""
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user = make_user(db)
        client = _client_for(user, db)

        resp = client.get("/api/watchlist")
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        _clear()
        db.close()


def test_watchlists_are_scoped_per_user():
    reset_tables("watchlists", "users")
    db = get_session()
    try:
        user_a = make_user(db, email="wl-a@example.test")
        user_b = make_user(db, email="wl-b@example.test")

        db.add(Watchlist(id=uuid.uuid4(), user_id=user_b.id,
                         keyword="Tesla", company_name="Tesla"))
        db.commit()

        client = _client_for(user_a, db)
        assert client.get("/api/watchlist").json() == [], (
            "User A must not see User B's watchlist"
        )
    finally:
        _clear()
        db.close()


def test_analyze_defaults_to_true_for_existing_callers():
    """Backward compatibility: omitting `analyze` must keep the old behaviour."""
    import inspect as _inspect
    from app.api.routes import watchlists as wl

    source = _inspect.getsource(wl.add_watchlist)
    assert 'data.get("analyze", True)' in source, (
        "The analyze flag must default to True so existing callers are unchanged."
    )
