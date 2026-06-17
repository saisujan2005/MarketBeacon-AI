import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ask import router as ask_router
from app.api.routes.notifications import router as notification_router
from app.api.routes.alerts import router as alert_router
from app.api.routes.trends import router as trends_router
from app.api.routes.market_summary import router as market_summary_router
from app.api.routes.watchlists import router as watchlist_router
from app.api.routes.twitter_follows import router as twitter_router
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

    # Start RSS news scheduler
    news_scheduler = start_scheduler(interval_minutes=10)

    # Start Twitter monitor scheduler
    twitter_scheduler = start_twitter_scheduler()

    yield

    logger.info("MarketBeacon AI shutting down...")
    news_scheduler.shutdown(wait=False)
    twitter_scheduler.shutdown(wait=False)


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

if _extra_routers:
    app.include_router(source_router)
    app.include_router(post_router)


@app.get("/")
def root():
    return {"message": "MarketBeacon AI API Running"}