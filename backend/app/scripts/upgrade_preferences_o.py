import logging
from sqlalchemy import text, inspect
from app.db.database import engine, SessionLocal
from app.models.base import Base

# Import all models to ensure they are registered with Base
from app.models.user import User, UserPreferences  # noqa: F401
from app.models.push_subscription import PushSubscription  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade_schema():
    logger.info("Starting Phase O notification preferences database upgrade...")
    
    # 1. Add notification preference columns to user_preferences if they don't exist
    inspector = inspect(engine)
    pref_cols = [c["name"] for c in inspector.get_columns("user_preferences")]
    
    new_cols = {
        "push_notifications": "BOOLEAN DEFAULT TRUE",
        "morning_brief": "BOOLEAN DEFAULT TRUE",
        "evening_summary": "BOOLEAN DEFAULT TRUE",
        "smart_alerts": "BOOLEAN DEFAULT TRUE",
        "watchlist_alerts": "BOOLEAN DEFAULT TRUE",
        "portfolio_alerts": "BOOLEAN DEFAULT TRUE",
        "weekly_digest": "BOOLEAN DEFAULT TRUE",
        "quiet_hours_enabled": "BOOLEAN DEFAULT FALSE",
        "quiet_hours_start": "VARCHAR DEFAULT '22:00'",
        "quiet_hours_end": "VARCHAR DEFAULT '08:00'",
        "timezone": "VARCHAR DEFAULT 'UTC'"
    }
    
    with engine.connect() as conn:
        with conn.begin():
            for col_name, col_type in new_cols.items():
                if col_name not in pref_cols:
                    logger.info(f"Adding column '{col_name}' to 'user_preferences' table...")
                    conn.execute(text(f"ALTER TABLE user_preferences ADD COLUMN {col_name} {col_type};"))
                    
    # 2. Create the push_subscriptions table if missing
    logger.info("Creating push_subscriptions table if missing...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database preferences and push tables updated successfully!")


if __name__ == "__main__":
    upgrade_schema()
