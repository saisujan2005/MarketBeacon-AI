import logging
import uuid
from sqlalchemy import text, inspect
from app.db.database import engine, SessionLocal
from app.models.base import Base

# Import all models to ensure they are registered
from app.models.user import User, UserPreferences
from app.models.post import Post  # noqa: F401
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.chat import ChatSession
from app.models.research_document import ResearchDocument
from app.models.research_metric import ResearchMetric
from app.models.research_cache import CompanyPeerCache, CompanyResearchCache
from app.models.watchlist import Watchlist
from app.models.daily_briefing import DailyBriefing
from app.models.holding import Holding  # noqa: F401
from app.models.research_workspace import ResearchWorkspace  # noqa: F401
from app.services.auth_service import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade_and_backfill_auth():
    logger.info("Starting SaaS Auth database migration...")
    
    # 1. Defensively create all tables including users & user_preferences
    Base.metadata.create_all(bind=engine)
    logger.info("Base tables verified and created.")
    
    db = SessionLocal()
    try:
        # 2. Check if a default user exists, otherwise create it
        default_email = "sujan@marketbeacon.ai"
        default_user = db.query(User).filter(User.email == default_email).first()
        
        if not default_user:
            logger.info("Creating default system user (Sujan) for database backfilling...")
            # Default password: Sujan@2005 (matches env settings)
            pwd_hash = hash_password("Sujan@2005")
            default_user = User(
                id=uuid.uuid4(),
                full_name="Sujan",
                email=default_email,
                password_hash=pwd_hash,
                role="admin",
                is_verified=True,
                preferred_market="US",
                subscription_plan="pro"
            )
            db.add(default_user)
            db.flush()
            
            # Create user preferences
            prefs = UserPreferences(
                user_id=default_user.id,
                theme="dark",
                language="en",
                default_ai_model="llama-3.3-70b-versatile",
                market_region="US"
            )
            db.add(prefs)
            db.commit()
            logger.info(f"Default user created with ID: {default_user.id}")
        else:
            logger.info(f"Default user (Sujan) already exists with ID: {default_user.id}")
            
        default_user_id = str(default_user.id)
        
        # 3. Add user_id column to existing tables defensively
        tables_to_add_user_id = [
            "chat_sessions",
            "research_documents",
            "research_metrics",
            "company_peer_caches",
            "company_research_caches",
            "watchlists",
            "notifications",
            "daily_briefings",
            "alerts"
        ]
        
        inspector = inspect(engine)
        
        for table_name in tables_to_add_user_id:
            columns = [c["name"] for c in inspector.get_columns(table_name)]
            if "user_id" not in columns:
                logger.info(f"Adding user_id to table: {table_name}")
                with engine.connect() as conn:
                    with conn.begin():
                        # Add column as nullable first
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS user_id UUID;"))
                        
                        # Set default user_id for existing rows
                        conn.execute(text(f"UPDATE {table_name} SET user_id = '{default_user_id}' WHERE user_id IS NULL;"))
                        
                        # Add foreign key constraint
                        constraint_name = f"fk_{table_name}_user_id"
                        conn.execute(text(
                            f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} "
                            f"FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;"
                        ))
                        
                        # Make user_id NOT NULL
                        conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN user_id SET NOT NULL;"))
                logger.info(f"Successfully migrated table: {table_name}")
            else:
                logger.info(f"Column user_id already exists in table: {table_name}")
                
        # 3.5. Add Watchlist columns (sector, industry, priority, added_at, last_analyzed_at)
        logger.info("Verifying watchlists table columns...")
        watchlist_cols = [c["name"] for c in inspector.get_columns("watchlists")]
        with engine.connect() as conn:
            with conn.begin():
                if "sector" not in watchlist_cols:
                    logger.info("Adding sector column to watchlists table...")
                    conn.execute(text("ALTER TABLE watchlists ADD COLUMN sector VARCHAR;"))
                if "industry" not in watchlist_cols:
                    logger.info("Adding industry column to watchlists table...")
                    conn.execute(text("ALTER TABLE watchlists ADD COLUMN industry VARCHAR;"))
                if "priority" not in watchlist_cols:
                    logger.info("Adding priority column to watchlists table...")
                    conn.execute(text("ALTER TABLE watchlists ADD COLUMN priority INTEGER DEFAULT 3;"))
                if "added_at" not in watchlist_cols:
                    logger.info("Adding added_at column to watchlists table...")
                    conn.execute(text("ALTER TABLE watchlists ADD COLUMN added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
                if "last_analyzed_at" not in watchlist_cols:
                    logger.info("Adding last_analyzed_at column to watchlists table...")
                    conn.execute(text("ALTER TABLE watchlists ADD COLUMN last_analyzed_at TIMESTAMP;"))
                if "analysis_cache" not in watchlist_cols:
                    logger.info("Adding analysis_cache column to watchlists table...")
                    conn.execute(text("ALTER TABLE watchlists ADD COLUMN analysis_cache JSON;"))
                
        # 4. Handle unique constraints on caches
        # For company_peer_caches: make sure we drop the old unique on company_name if it exists
        try:
            with engine.connect() as conn:
                with conn.begin():
                    # PostgreSQL: check constraints and drop unique if it's there
                    conn.execute(text("ALTER TABLE company_peer_caches DROP CONSTRAINT IF EXISTS company_peer_caches_company_name_key;"))
                    conn.execute(text("ALTER TABLE company_peer_caches DROP CONSTRAINT IF EXISTS uq_user_company_peer;"))
                    conn.execute(text("ALTER TABLE company_peer_caches ADD CONSTRAINT uq_user_company_peer UNIQUE (user_id, company_name);"))
                    
                    conn.execute(text("ALTER TABLE company_research_caches DROP CONSTRAINT IF EXISTS uq_user_company_research;"))
                    conn.execute(text("ALTER TABLE company_research_caches ADD CONSTRAINT uq_user_company_research UNIQUE (user_id, company_name);"))
            logger.info("Updated unique constraints on cache tables.")
        except Exception as ec:
            logger.warning(f"Could not alter cache constraints: {ec}")
            
        logger.info("SaaS Auth database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during Auth DB upgrade: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    upgrade_and_backfill_auth()
