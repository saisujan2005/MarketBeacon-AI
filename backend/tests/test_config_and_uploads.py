"""
P0.2 / P0.8 / P0.10 - Secret handling, upload paths, and removal of the exec bridge.
"""

import inspect
from pathlib import Path

from app.core.config import Settings, settings
from app.api.routes.copilot import _safe_filename, ALLOWED_UPLOAD_EXTENSIONS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ── P0.2 secrets ─────────────────────────────────────────────────────────────

# These guards assert STRUCTURAL properties rather than matching the historical
# secret literals, so the credentials are not re-introduced into the repository
# by the very test that exists to keep them out.

def test_no_hardcoded_jwt_secret_default():
    from app.services import auth_service

    source = inspect.getsource(auth_service)
    assert 'os.getenv("JWT_SECRET"' not in source, (
        "auth_service must read the secret from validated config, not os.getenv with a default."
    )
    assert "JWT_SECRET = settings.JWT_SECRET" in source, (
        "The JWT secret must come from app.core.config."
    )
    # No string literal may be assigned to the signing key.
    assert 'JWT_SECRET = "' not in source and "JWT_SECRET = '" not in source, (
        "A hardcoded JWT signing key literal must never be present."
    )


def test_no_hardcoded_database_credentials():
    from app.db import database

    source = inspect.getsource(database)
    # A connection URL literal would necessarily embed a credential.
    assert "postgresql" not in source.lower(), (
        "No database connection URL literal may appear in database.py."
    )
    assert "settings.DATABASE_URL" in source, (
        "The database URL must come from validated config."
    )


def test_production_requires_secrets(monkeypatch_env=None):
    """In production, missing JWT_SECRET/DATABASE_URL must abort startup."""
    import os
    from app.core.config import MissingConfigError

    saved = {k: os.environ.get(k) for k in ("APP_ENV", "JWT_SECRET", "DATABASE_URL")}
    try:
        os.environ["APP_ENV"] = "production"
        os.environ.pop("JWT_SECRET", None)
        os.environ["DATABASE_URL"] = "postgresql://u:p@localhost:5432/x"

        raised = False
        try:
            Settings()
        except MissingConfigError:
            raised = True
        assert raised, "Production must fail fast when JWT_SECRET is missing."

        # A too-short secret is also rejected.
        os.environ["JWT_SECRET"] = "short"
        raised = False
        try:
            Settings()
        except MissingConfigError:
            raised = True
        assert raised, "Production must reject a weak JWT_SECRET."
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_describe_never_exposes_secret_values():
    described = settings.describe()
    flat = str(described)
    assert settings.JWT_SECRET not in flat, "describe() must not include the JWT secret."
    if settings.DATABASE_URL:
        assert settings.DATABASE_URL not in flat, "describe() must not include the database URL."
    assert described["jwt_secret_configured"] in (True, False)


def test_cors_has_no_wildcard_vercel_regex():
    from app.main import app

    for mw in app.user_middleware:
        opts = getattr(mw, "kwargs", {}) or {}
        assert not opts.get("allow_origin_regex"), (
            "Wildcard CORS origin regex must be removed."
        )
        origins = opts.get("allow_origins")
        if origins:
            assert "*" not in origins


# ── P0.10 uploads ────────────────────────────────────────────────────────────

def test_no_hardcoded_windows_upload_path():
    from app.api.routes import copilot

    source = inspect.getsource(copilot)
    assert "d:/MarketBeacon-AI" not in source.lower(), (
        "Hardcoded Windows upload path must be gone."
    )


def test_upload_dir_is_configurable_and_absolute():
    assert isinstance(settings.UPLOAD_DIR, Path)
    # Default resolves under backend/, and works on both Windows and Linux.
    assert settings.UPLOAD_DIR.is_absolute() or not str(settings.UPLOAD_DIR).startswith("d:")


def test_filename_sanitisation_blocks_traversal():
    assert _safe_filename("../../etc/passwd") == "passwd"
    assert _safe_filename("..\\..\\windows\\system32\\cfg.txt") == "cfg.txt"
    assert _safe_filename("report.pdf") == "report.pdf"
    assert _safe_filename("my report (final).docx") == "my_report__final_.docx"
    assert _safe_filename("") == "upload"
    assert "/" not in _safe_filename("a/b/c.txt")
    assert "\\" not in _safe_filename("a\\b\\c.txt")


def test_upload_path_stays_inside_upload_dir():
    uploads = Path(settings.UPLOAD_DIR)
    for hostile in ["../../etc/passwd", "..\\..\\evil.txt", "ok.pdf"]:
        candidate = (uploads / f"doc-id_{_safe_filename(hostile)}").resolve()
        assert str(candidate).startswith(str(uploads.resolve())), (
            f"Upload path escaped the upload directory: {candidate}"
        )


def test_upload_size_limit_configured():
    assert settings.MAX_UPLOAD_MB > 0
    assert settings.max_upload_bytes == settings.MAX_UPLOAD_MB * 1024 * 1024

    source = inspect.getsource(__import__("app.api.routes.copilot", fromlist=["x"]))
    assert "max_upload_bytes" in source, "Upload handler must enforce a size limit."
    assert "413" in source


def test_allowed_extensions_unchanged():
    assert ALLOWED_UPLOAD_EXTENSIONS == {".pdf", ".docx", ".txt"}


# ── P0.8 vite bridge ─────────────────────────────────────────────────────────

def test_vite_config_has_no_command_execution_bridge():
    vite = (REPO_ROOT / "frontend" / "vite.config.js").read_text(encoding="utf-8")
    for forbidden in ["execSync(", "spawn(", "taskkill", "run_cmd.txt"]:
        assert forbidden not in vite, (
            f"vite.config.js still contains '{forbidden}'."
        )


# ── P0.1 destructive startup code ────────────────────────────────────────────

def test_no_destructive_startup_code():
    from app import main

    source = inspect.getsource(main)
    assert "jaya7905" not in source, "Hardcoded user deletion must be gone."
    assert "db.delete(" not in source, "Startup must not delete database rows."
    assert "debug-watchlist" not in source, "Debug endpoint must be gone."
    assert "traceback" not in source, "Startup must not expose tracebacks."


def test_no_hardcoded_admin_password_in_migrations():
    """
    The startup migration must never hash a password literal. It previously
    created an admin account with a password committed to the repository.
    """
    from app.scripts import upgrade_auth_db

    source = inspect.getsource(upgrade_auth_db)
    assert 'hash_password("' not in source and "hash_password('" not in source, (
        "The migration must not hash a hardcoded password literal."
    )
    assert "BOOTSTRAP_ADMIN_PASSWORD" in source, (
        "Admin bootstrap must be opt-in via environment variables."
    )
    assert 'os.getenv("BOOTSTRAP_ADMIN_PASSWORD")' in source, (
        "The bootstrap password must come from the environment."
    )
