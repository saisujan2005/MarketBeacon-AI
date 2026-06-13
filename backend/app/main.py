from fastapi import FastAPI
from app.api.sources import router as source_router
from app.api.posts import router as post_router
from app.api.routes.ask import router as ask_router
from app.api.routes.notifications import (
    router as notification_router
)
from app.api.routes.alerts import router as alert_router

from app.api.routes.trends import (
    router as trends_router
)

from app.api.routes.market_summary import (
    router as market_summary_router
)


app = FastAPI(
    title="MarketBeacon AI"
)

app.include_router(
    ask_router,
    tags=["MarketBeacon"]
)

app.include_router(
    notification_router
)

app.include_router(
    trends_router
)

app.include_router(
    market_summary_router
)

app.include_router(alert_router)

app.include_router(source_router)
app.include_router(post_router)


@app.get("/")
def root():
    return {
        "message": "MarketBeacon AI API Running"
    }