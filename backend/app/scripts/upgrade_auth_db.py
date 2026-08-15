import logging
import os
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


def _bootstrap_admin_if_requested(db):
    """
    Optionally create an initial administrator account.

    Only runs when BOTH BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD are
    present in the environment, and only when that account does not already
    exist. Nothing is created implicitly, and no password literal exists in the
    source tree. The password is never logged.
    """
    email = (os.getenv("BOOTSTRAP_ADMIN_EMAIL") or "").strip().lower()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or ""

    if not email or not password:
        return None

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        logger.info("Bootstrap admin already exists; leaving it unchanged.")
        return existing

    if len(password) < 12:
        logger.error("BOOTSTRAP_ADMIN_PASSWORD must be at least 12 characters. Skipping bootstrap.")
        return None

    admin = User(
        id=uuid.uuid4(),
        full_name=os.getenv("BOOTSTRAP_ADMIN_NAME") or "Administrator",
        email=email,
        password_hash=hash_password(password),
        role="admin",
        is_verified=True,
    )
    db.add(admin)
    db.flush()
    db.add(UserPreferences(user_id=admin.id))
    db.commit()
    logger.info("Bootstrap administrator account created.")
    return admin


def upgrade_and_backfill_auth():
    logger.info("Starting SaaS Auth database migration...")
    
    # 1. Defensively create all tables including users & user_preferences
    Base.metadata.create_all(bind=engine)
    logger.info("Base tables verified and created.")
    
    db = SessionLocal()
    try:
        # 2. Determine an owner account used to backfill legacy rows.
        #
        # This previously created a hardcoded admin account
        # (sujan@marketbeacon.ai / a literal password committed to the repo) on
        # every startup, which is a permanent backdoor on any deployment.
        #
        # Now: an admin is only bootstrapped when BOTH BOOTSTRAP_ADMIN_EMAIL and
        # BOOTSTRAP_ADMIN_PASSWORD are supplied via the environment. Otherwise we
        # reuse the oldest existing account purely as the backfill owner.
        default_user = _bootstrap_admin_if_requested(db)

        if not default_user:
            default_user = db.query(User).order_by(User.created_at.asc()).first()

        default_user_id = str(default_user.id) if default_user else None
        if default_user_id:
            logger.info("Using existing account as backfill owner for legacy rows.")
        else:
            logger.warning(
                "No user accounts exist yet; legacy rows will not be backfilled and "
                "user_id columns will remain nullable until an account is created."
            )

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

                        # Backfill existing rows only when an owner account exists.
                        if default_user_id:
                            conn.execute(
                                text(f"UPDATE {table_name} SET user_id = :uid WHERE user_id IS NULL;"),
                                {"uid": default_user_id},
                            )

                        # Add foreign key constraint
                        constraint_name = f"fk_{table_name}_user_id"
                        conn.execute(text(
                            f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} "
                            f"FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;"
                        ))

                        # Only enforce NOT NULL when every row actually has an owner,
                        # otherwise the migration would fail and abort startup.
                        remaining = conn.execute(
                            text(f"SELECT COUNT(*) FROM {table_name} WHERE user_id IS NULL;")
                        ).scalar()
                        if remaining == 0:
                            conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN user_id SET NOT NULL;"))
                        else:
                            logger.warning(
                                "%s still has %s rows without user_id; leaving column nullable.",
                                table_name, remaining,
                            )
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
