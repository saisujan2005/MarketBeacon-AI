import logging
from sqlalchemy import text
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)

def upgrade_db():
    db = SessionLocal()
    try:
        # PostgreSQL syntax to add columns if they don't exist
        queries = [
            "ALTER TABLE posts ADD COLUMN IF NOT EXISTS impact_level VARCHAR;",
            "ALTER TABLE posts ADD COLUMN IF NOT EXISTS reasoning TEXT;",
            "ALTER TABLE posts ADD COLUMN IF NOT EXISTS confidence INTEGER;",
            "ALTER TABLE posts ADD COLUMN IF NOT EXISTS affected_assets JSON;"
        ]
        
        for q in queries:
            try:
                db.execute(text(q))
                db.commit()
                print(f"Executed: {q}")
            except Exception as e:
                db.rollback()
                print(f"Notice: {e}")
                
        print("Database upgraded successfully. Added impact_level, reasoning, confidence, and affected_assets columns to posts table.")
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade_db()
