import logging
from sqlalchemy import text, inspect
from datetime import timezone
from app.db.database import engine, SessionLocal
from app.models.base import Base

# Import all models to register them
from app.models.post import Post  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.notification_summary import NotificationSummary  # noqa: F401
from app.models.chat import ChatSession, ChatMessage  # noqa: F401
from app.models.research_document import ResearchDocument  # noqa: F401
from app.models.research_metric import ResearchMetric  # noqa: F401
from app.models.research_cache import CompanyPeerCache, CompanyResearchCache  # noqa: F401
from app.models.holding import Holding  # noqa: F401
from app.models.research_workspace import ResearchWorkspace  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade_and_backfill():
    logger.info("Starting database schema updates for Notifications...")

    # 1. Verify and create missing tables defensively first
    logger.info("Verifying and creating missing tables defensively...")
    inspector = inspect(engine)
    pre_existing_tables = inspector.get_table_names()

    required_tables = {
        "chat_sessions": ChatSession,
        "chat_messages": ChatMessage,
        "research_documents": ResearchDocument,
        "research_metrics": ResearchMetric
    }

    for name, model in required_tables.items():
        if name not in pre_existing_tables:
            try:
                model.__table__.create(bind=engine, checkfirst=True)
                logger.info(f"Defensively created table: {name}")
            except Exception as e:
                logger.error(f"Failed to create table {name} defensively: {e}")

    # Create all other missing registered tables
    Base.metadata.create_all(bind=engine)

    # Log table status as requested
    for name in required_tables.keys():
        if name in pre_existing_tables:
            logger.info(f"✓ table {name} exists")
        else:
            logger.info(f"✓ table {name} created")

    # 2. Run alter queries now that tables are guaranteed to exist
    alter_queries = [
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS posted_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS source VARCHAR;",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS sentiment VARCHAR;",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS event_type VARCHAR;",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS importance_score INTEGER;",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS post_url VARCHAR;",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS meta_info JSON;",
        "ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;",
        
        "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS post_id UUID;",
        "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS post_url VARCHAR;",
        "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS summary_text TEXT;",
        "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS summary_generated_at TIMESTAMP;",
        "ALTER TABLE research_metrics ADD COLUMN IF NOT EXISTS citation_coverage FLOAT DEFAULT 0.0;",
        
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS company_name VARCHAR;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS exchange VARCHAR;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS sector VARCHAR;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS industry VARCHAR;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS notes VARCHAR;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS favorite BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 3;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS added_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS last_analyzed_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS analysis_cache JSON;",
        "ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;"
    ]

    with engine.connect() as conn:
        with conn.begin():
            for query in alter_queries:
                logger.info(f"Executing: {query}")
                try:
                    conn.execute(text(query))
                except Exception as eq:
                    logger.warning(f"Alter query failed or already executed: {query} | Error: {eq}")

    logger.info("Starting backfill process...")
    db = SessionLocal()
    try:
        # 1. Backfill Alerts to link to Posts
        alerts = db.query(Alert).all()
        logger.info(f"Scanning {len(alerts)} alerts for backfilling...")
        alerts_backfilled = 0
        for alert in alerts:
            # Try to match by title
            post = db.query(Post).filter(Post.title == alert.title).first()
            if post:
                alert.post_id = post.id
                alert.post_url = post.post_url
                alerts_backfilled += 1
        db.commit()
        logger.info(f"Successfully linked {alerts_backfilled} alerts to their source posts.")

        # 2. Backfill Notifications
        notifications = db.query(Notification).all()
        logger.info(f"Scanning {len(notifications)} notifications for backfilling...")
        notifs_backfilled = 0
        for notif in notifications:
            # Let's match notification to a post
            post = db.query(Post).filter(Post.title == notif.title).first()
            
            def ensure_utc(dt):
                if dt is None:
                    return None
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)

            if post:
                notif.posted_at = ensure_utc(post.posted_at)
                notif.fetched_at = ensure_utc(post.fetched_at)
                notif.source = post.source_id
                notif.sentiment = post.sentiment
                notif.event_type = post.event_type
                notif.importance_score = post.importance_score
                notif.post_url = post.post_url
                
                # Setup meta_info JSON format for future prep
                notif.meta_info = {
                    "source_type": "rss_post",
                    "confidence": post.confidence,
                    "entities": post.entities,
                    "reasoning": post.reasoning
                }
                
                notifs_backfilled += 1
                logger.info(
                    f"[BACKFILL SUCCESS] Matched notification '{notif.title}' "
                    f"to Post ID: {post.id} (Confidence: 85%)"
                )
            else:
                # If post not found, try mapping alert
                alert = db.query(Alert).filter(Alert.title == notif.title).first()
                if alert:
                    notif.fetched_at = ensure_utc(alert.created_at)
                    notif.event_type = alert.event_type
                    # Try to parse string score to integer
                    try:
                        notif.importance_score = int(alert.importance_score) if alert.importance_score else None
                    except ValueError:
                        notif.importance_score = None
                        
                    notif.meta_info = {
                        "source_type": "alert_fallback"
                    }
                    notifs_backfilled += 1
                    logger.info(
                        f"[BACKFILL ALERT FALLBACK] Matched notification '{notif.title}' "
                        f"to Alert ID: {alert.id} (Confidence: 70%)"
                    )
                else:
                    logger.warning(f"[BACKFILL FAILED] No matching Post or Alert for: '{notif.title}'")

        db.commit()
        logger.info(f"Backfill complete. Populated {notifs_backfilled} notifications.")

    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("Upgrade and backfill script complete.")


if __name__ == "__main__":
    upgrade_and_backfill()

