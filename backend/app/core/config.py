"""
Centralised application configuration.

Values are read from environment variables (loaded from a local `.env` during
development via python-dotenv, exactly as the rest of the project already does).

Design rules:
  * Secrets have NO hardcoded fallback values. A committed default signing key or
    database password is equivalent to publishing it.
  * In production (APP_ENV=production) the process refuses to start when a
    required secret is missing, rather than silently running on a weak default.
  * In development a missing JWT secret produces a random per-process key plus a
    warning, so local work keeps functioning without anything sensitive in git.
  * Secret *values* are never logged. Only their presence/absence is reported.
"""

import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# backend/app/core/config.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load the project-root .env (development convenience). On Render/production the
# environment is already populated, and load_dotenv() will simply find no file.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "yes", "on")


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid integer for %s; falling back to %s", name, default)
        return default


class MissingConfigError(RuntimeError):
    """Raised at startup when a required production secret is absent."""


class Settings:
    """Process-wide configuration singleton."""

    def __init__(self) -> None:
        self.APP_ENV: str = (os.getenv("APP_ENV") or "development").strip().lower()

        # ── Database ────────────────────────────────────────────────────────
        # No default: the previous hardcoded localhost URL embedded a real password.
        self.DATABASE_URL: str | None = os.getenv("DATABASE_URL") or None

        # ── Auth ────────────────────────────────────────────────────────────
        self.JWT_SECRET: str | None = os.getenv("JWT_SECRET") or None
        self.JWT_ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 15)
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = _get_int("REFRESH_TOKEN_EXPIRE_DAYS", 7)

        # ── LLM ─────────────────────────────────────────────────────────────
        self.GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY") or None
        self.GROQ_MODEL: str = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"

        # ── Uploads ─────────────────────────────────────────────────────────
        # Configurable so the same code runs on Windows dev and Linux/Render.
        upload_dir = os.getenv("UPLOAD_DIR")
        self.UPLOAD_DIR: Path = (
            Path(upload_dir).expanduser() if upload_dir else BACKEND_DIR / "uploads"
        )
        self.MAX_UPLOAD_MB: int = _get_int("MAX_UPLOAD_MB", 25)

        # ── Frontend / CORS ─────────────────────────────────────────────────
        self.FRONTEND_URL: str = os.getenv("FRONTEND_URL") or "http://localhost:5173"

        # ── Pipeline tuning ─────────────────────────────────────────────────
        self.NEWS_INTERVAL_MINUTES: int = _get_int("NEWS_INTERVAL_MINUTES", 10)

        # Per-feed HTTP timeout (connect + read). feedparser has no timeout of
        # its own, so without this one unresponsive host stalls the whole run.
        self.RSS_FETCH_TIMEOUT_SECONDS: int = _get_int("RSS_FETCH_TIMEOUT_SECONDS", 15)

        # Run the first ingestion pass on boot (scheduled immediately, never
        # blocking startup). Set false to wait for the first interval instead.
        self.RUN_INGESTION_ON_STARTUP: bool = _get_bool("RUN_INGESTION_ON_STARTUP", True)

        # Alert firing threshold: a post alerts when importance_score > this.
        #
        # Deliberately NOT read from the legacy ALERT_THRESHOLD variable. That
        # variable is documented in .env.example but has never been used by the
        # code, which hardcoded 80. Wiring it up here would silently change alert
        # behaviour for existing deployments (e.g. an .env with ALERT_THRESHOLD=85
        # would start suppressing alerts). Making it configurable is deferred;
        # this key exists so the value is no longer a magic number.
        self.ALERT_IMPORTANCE_THRESHOLD: int = _get_int("ALERT_IMPORTANCE_THRESHOLD", 80)

        self.DISABLE_LOCAL_ML: bool = _get_bool("DISABLE_LOCAL_ML", False)

        # Optional startup preloading of research caches (off by default: it made
        # every boot fire LLM calls for a hardcoded account).
        self.ENABLE_STARTUP_PRELOAD: bool = _get_bool("ENABLE_STARTUP_PRELOAD", False)

        self._validate()

    # ── Derived helpers ─────────────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        return self.APP_ENV in ("production", "prod")

    @property
    def cors_origins(self) -> list[str]:
        """Explicit CORS allowlist built from FRONTEND_URL (comma separated)."""
        origins: list[str] = []
        if not self.is_production:
            origins.extend(
                [
                    "http://localhost:5173",
                    "http://localhost:3000",
                    "http://127.0.0.1:5173",
                ]
            )
        for url in (self.FRONTEND_URL or "").split(","):
            url = url.strip().rstrip("/")
            if url and url not in origins:
                origins.append(url)
        return origins

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    # ── Validation ──────────────────────────────────────────────────────────

    def _validate(self) -> None:
        """Fail fast in production; degrade safely (and loudly) in development."""
        missing: list[str] = []

        if not self.DATABASE_URL:
            missing.append("DATABASE_URL")

        if self.is_production:
            if not self.JWT_SECRET:
                missing.append("JWT_SECRET")
            elif len(self.JWT_SECRET) < 32:
                raise MissingConfigError(
                    "JWT_SECRET must be at least 32 characters in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            if missing:
                raise MissingConfigError(
                    "Missing required production configuration: "
                    + ", ".join(missing)
                    + ". Set these environment variables before starting the service."
                )
        else:
            if missing:
                raise MissingConfigError(
                    "Missing required configuration: "
                    + ", ".join(missing)
                    + ". Copy .env.example to .env and fill in the values."
                )
            if not self.JWT_SECRET:
                # Ephemeral development key. Never persisted, never logged.
                self.JWT_SECRET = secrets.token_urlsafe(64)
                logger.warning(
                    "JWT_SECRET is not set. Generated a temporary development key; "
                    "all sessions will be invalidated on restart. Set JWT_SECRET in .env "
                    "for a stable local session."
                )

        if not self.GROQ_API_KEY:
            # Not fatal: the app degrades to rule-based fallbacks without an LLM.
            logger.warning("GROQ_API_KEY is not set. LLM-backed features will be unavailable.")

    def describe(self) -> dict:
        """Non-sensitive configuration summary, safe to log."""
        return {
            "app_env": self.APP_ENV,
            "database_url_configured": bool(self.DATABASE_URL),
            "jwt_secret_configured": bool(self.JWT_SECRET),
            "groq_api_key_configured": bool(self.GROQ_API_KEY),
            "groq_model": self.GROQ_MODEL,
            "upload_dir": str(self.UPLOAD_DIR),
            "max_upload_mb": self.MAX_UPLOAD_MB,
            "cors_origins": self.cors_origins,
            "alert_importance_threshold": self.ALERT_IMPORTANCE_THRESHOLD,
            "disable_local_ml": self.DISABLE_LOCAL_ML,
        }


settings = Settings()
