import logging
import os
from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware


from app.api.routes.ask import router as ask_router
from app.api.routes.notifications import router as notification_router
from app.api.routes.alerts import router as alert_router
from app.api.routes.trends import router as trends_router
from app.api.routes.market_summary import router as market_summary_router
from app.api.routes.watchlists import router as watchlist_router
from app.api.routes.twitter_follows import router as twitter_router
from app.api.routes.sectors import router as sectors_router
from app.api.routes.timeline import router as timeline_router
from app.api.routes.daily_briefing import router as daily_briefing_router
from app.api.routes.research_reports import router as research_reports_router
from app.api.routes.admin import router as admin_router
from app.api.routes.copilot import router as copilot_router
from app.api.routes.auth import router as auth_router
from app.api.routes.explain import router as explain_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.workspace import router as workspace_router
from app.core.config import settings
from app.scheduler.news_scheduler import start_scheduler
from app.scheduler.twitter_scheduler import start_twitter_scheduler

try:
    from app.api.sources import router as source_router
    from app.api.posts import router as post_router
    _extra_routers = True
except ImportError:
    _extra_routers = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MarketBeacon AI starting up...")

    # Run DB migration and backfill
    try:
        from app.scripts.upgrade_notifications import upgrade_and_backfill
        upgrade_and_backfill()
        
        # Run Auth and SaaS DB migrations
        from app.scripts.upgrade_auth_db import upgrade_and_backfill_auth
        upgrade_and_backfill_auth()

        # Run Preferences and Push Notification migrations
        from app.scripts.upgrade_preferences_o import upgrade_schema
        upgrade_schema()

        # P0 hardening: alert-queue column, research report ownership,
        # importance_score type fix, and critical indexes. Idempotent.
        from app.scripts.upgrade_p0_hardening import upgrade_p0_hardening
        upgrade_p0_hardening()


        _migration_log = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "migration_status.log")
        with open(_migration_log, "w") as f:
            f.write("Migration status: SUCCESS\n")
    except Exception as e:
        logger.error(f"Failed to run notifications database upgrade: {e}")
        _migration_log = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "migration_status.log")
        with open(_migration_log, "w") as f:
            f.write(f"Migration status: FAILED | Error: {e}\n")

    # Initialize Qdrant collections
    try:
        from app.embeddings.qdrant_service import create_collection
        create_collection()
        logger.info("Qdrant collections initialized successfully.")
    except Exception as e:
        logger.error(
            "\n" + "="*80 + "\n"
            "CRITICAL WARNING: Qdrant database initialization failed!\n"
            f"Error details: {e}\n"
            "The local Qdrant database folder is locked or inaccessible. Vector search and document uploads will be disabled,\n"
            "but the core API server will continue running. Please resolve the lock if this is unexpected.\n" +
            "="*80 + "\n"
        )

    # Start background schedulers. Both return immediately; ingestion runs on
    # their worker threads. A scheduler failure must never stop the API from
    # coming up, so each is guarded and the failure is logged loudly.
    news_scheduler = None
    twitter_scheduler = None

    try:
        news_scheduler = start_scheduler(interval_minutes=settings.NEWS_INTERVAL_MINUTES)
    except Exception as e:
        logger.exception("Failed to start the news scheduler; API will run without RSS ingestion: %s", e)

    try:
        twitter_scheduler = start_twitter_scheduler()
    except Exception as e:
        logger.exception("Failed to start the Twitter scheduler; API will run without tweet monitoring: %s", e)

    # Optional cache warming. Disabled by default: it previously ran LLM-backed
    # dossier generation for a hardcoded account on every single boot.
    if settings.ENABLE_STARTUP_PRELOAD:
        import threading

        def run_preloading():
            from app.db.database import SessionLocal
            from app.services.research_agent import preload_frequent_companies
            db = SessionLocal()
            try:
                preload_frequent_companies(db)
            except Exception as pe:
                logger.error(f"Error in background cache preloading: {pe}")
            finally:
                db.close()

        threading.Thread(target=run_preloading, daemon=True).start()

    logger.info("Startup configuration: %s", settings.describe())

    yield

    logger.info("MarketBeacon AI shutting down...")
    for name, sched in (("news", news_scheduler), ("twitter", twitter_scheduler)):
        if sched is None:
            continue
        try:
            sched.shutdown(wait=False)
        except Exception as e:
            logger.warning("Error shutting down the %s scheduler: %s", name, e)
    
    # Close shared QdrantClient singleton and release files lock
    try:
        from app.embeddings.qdrant_service import close_qdrant_client
        close_qdrant_client()
        logger.info("Qdrant client connection closed and lock released successfully.")
    except Exception as e:
        logger.error(f"Failed to close Qdrant client: {e}")


app = FastAPI(
    title="MarketBeacon AI",
    lifespan=lifespan
)

# Explicit allowlist only. The previous `https://.*\.vercel\.app` regex allowed
# any Vercel-hosted site to make credentialed cross-origin requests.
# Add production frontend origins via the FRONTEND_URL env var (comma separated).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask_router,            tags=["Ask"])
app.include_router(alert_router,          tags=["Alerts"])
app.include_router(notification_router,   tags=["Notifications"])
app.include_router(trends_router,         tags=["Trends"])
app.include_router(market_summary_router, tags=["Summary"])
app.include_router(watchlist_router,      tags=["Watchlists"])
app.include_router(twitter_router)
app.include_router(sectors_router,         tags=["Sectors"])
app.include_router(timeline_router,        tags=["Timeline"])
app.include_router(daily_briefing_router,  tags=["Daily Briefing"])
app.include_router(research_reports_router,tags=["Research Reports"])
app.include_router(admin_router)
app.include_router(copilot_router,        tags=["Copilot"])
app.include_router(auth_router)
app.include_router(explain_router, tags=["Explain"])
app.include_router(portfolio_router, tags=["Portfolio"])
app.include_router(workspace_router, tags=["Workspace"])

if _extra_routers:
    app.include_router(source_router)
    app.include_router(post_router)


@app.get("/api/health")
def health():
    """Public liveness probe. Intentionally exposes no internal detail."""
    return {
        "status": "healthy",
        "service": "MarketBeacon AI"
    }


@app.get("/")
def root():
    return {"message": "MarketBeacon AI API Running"}