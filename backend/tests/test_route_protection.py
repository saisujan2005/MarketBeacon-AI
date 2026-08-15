"""
P0.3 - Route authentication and admin RBAC.

These tests inspect the live FastAPI dependency graph, so they automatically
cover any route added later; nothing has to be listed by hand.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.db.dependencies import get_current_user, require_admin

# Endpoints that are legitimately public.
PUBLIC_PATHS = {
    "/",
    "/api/health",
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/refresh",
}


def _route_dependencies(route):
    found = set()
    stack = [route.dependant]
    while stack:
        d = stack.pop()
        if d.call is not None:
            found.add(d.call)
        stack.extend(d.dependencies)
    return found


def _api_routes():
    return [r for r in app.routes if hasattr(r, "dependant") and hasattr(r, "path")]


def test_every_non_public_route_requires_authentication():
    unprotected = []
    for route in _api_routes():
        if route.path in PUBLIC_PATHS:
            continue
        if get_current_user not in _route_dependencies(route):
            unprotected.append(f"{sorted(route.methods)} {route.path}")

    assert not unprotected, (
        "These routes do not require authentication:\n  " + "\n  ".join(sorted(unprotected))
    )


def test_admin_routes_require_admin_role():
    admin_paths = {"/admin/reprocess-posts"}
    for route in _api_routes():
        if route.path in admin_paths:
            deps = _route_dependencies(route)
            assert require_admin in deps, f"{route.path} is missing require_admin"


def test_destructive_admin_operation_is_not_exposed_over_get():
    for route in _api_routes():
        if route.path == "/admin/reprocess-posts":
            assert "GET" not in route.methods, (
                "reprocess-posts must not be reachable via GET (CSRF-triggerable)."
            )


def test_protected_routes_reject_anonymous_requests():
    client = TestClient(app)
    for method, path in [
        ("get", "/api/alerts"),
        ("get", "/api/notifications"),
        ("get", "/market-summary"),
        ("get", "/trends"),
        ("get", "/research-reports"),
        ("get", "/timeline/entities"),
        ("get", "/sectors/heatmap"),
        ("get", "/twitter/follows"),
        ("get", "/posts/"),
        ("get", "/sources/"),
        ("post", "/admin/reprocess-posts"),
        ("post", "/ask"),
    ]:
        resp = getattr(client, method)(path)
        assert resp.status_code in (401, 403), (
            f"{method.upper()} {path} returned {resp.status_code} without auth "
            f"(expected 401/403)"
        )


def test_debug_watchlist_endpoint_is_gone():
    client = TestClient(app)
    assert client.get("/api/debug-watchlist").status_code == 404


def test_health_endpoint_stays_public():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
