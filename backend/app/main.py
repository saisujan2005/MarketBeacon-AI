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

    # Start RSS news scheduler
    news_scheduler = start_scheduler(interval_minutes=10)

    # Start Twitter monitor scheduler
    twitter_scheduler = start_twitter_scheduler()

    # Preload frequent companies asynchronously in a background thread
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

    # Log all registered FastAPI routes during startup
    logger.info("Registered FastAPI Routes:")
    for route in app.routes:
        if hasattr(route, "path"):
            logger.info(f"  {route.path}")
        else:
            logger.info(f"  {route}")

    yield

    logger.info("MarketBeacon AI shutting down...")
    news_scheduler.shutdown(wait=False)
    twitter_scheduler.shutdown(wait=False)
    
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
    # Trigger database check reload
    return {
        "status": "healthy",
        "service": "MarketBeacon AI"
    }


@app.get("/api/debug-watchlist")
def debug_watchlist_route():
    import sys
    import os
    import traceback
    from app.db.database import SessionLocal
    from app.models.user import User
    from app.services.watchlist_service import add_watchlist_keyword, analyze_watchlist_company
    
    db = SessionLocal()
    res = {}
    try:
        user = db.query(User).filter(User.email == "sujan@marketbeacon.ai").first()
        if not user:
            return {"error": "Default user sujan@marketbeacon.ai not found"}
        
        # Try to add "Reliance Industries"
        w = add_watchlist_keyword(
            db,
            keyword="Reliance Industries",
            user_id=user.id,
            company_name="Reliance Industries",
            exchange="NSE"
        )
        res["watchlist_added"] = {
            "id": str(w.id),
            "keyword": w.keyword,
            "company_name": w.company_name
        }
        
        # Analyze watchlist company
        analysis = analyze_watchlist_company(db, w.id, user.id, force=True)
        res["analysis_keys"] = list(analysis.keys()) if analysis else None
        res["status"] = "success"
    except Exception as e:
        res["status"] = "error"
        res["error_type"] = type(e).__name__
        res["error_message"] = str(e)
        res["traceback"] = traceback.format_exc()
    finally:
        db.close()
    return res


@app.get("/")
def root():
    return {"message": "MarketBeacon AI API Running"}