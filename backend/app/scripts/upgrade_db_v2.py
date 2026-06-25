import logging
from sqlalchemy import text
from app.db.database import engine
from app.models.base import Base

# Import all models to ensure they are registered with Base
from app.models.post import Post  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.watchlist import Watchlist  # noqa: F401
from app.models.source import Source  # noqa: F401
from app.models.timeline_event import TimelineEvent  # noqa: F401
from app.models.daily_briefing import DailyBriefing  # noqa: F401
from app.models.research_report import ResearchReport  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade():
    logger.info("Starting database upgrade...")

    # 1. Add columns to posts if they do not exist
    alter_queries = [
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS sentiment VARCHAR;",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS sentiment_confidence DOUBLE PRECISION;",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS sentiment_reasoning TEXT;",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS entities JSON;",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS predicted_direction VARCHAR;",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS prediction_confidence DOUBLE PRECISION;",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS prediction_reasoning TEXT;"
    ]

    with engine.connect() as conn:
        with conn.begin():
            for query in alter_queries:
                logger.info(f"Executing: {query}")
                conn.execute(text(query))

    # 2. Create any missing tables (like timeline_events, daily_briefings, research_reports)
    logger.info("Creating any missing tables...")
    Base.metadata.create_all(bind=engine)

    logger.info("Database upgrade completed successfully!")


if __name__ == "__main__":
    upgrade()
