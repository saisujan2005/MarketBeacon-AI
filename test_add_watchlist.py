import sys
import os
import uuid
import traceback

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.db.database import SessionLocal
from app.models.user import User
from app.services.watchlist_service import add_watchlist_keyword, analyze_watchlist_company

def run_test():
    db = SessionLocal()
    try:
        # Find default user sujan@marketbeacon.ai
        user = db.query(User).filter(User.email == "sujan@marketbeacon.ai").first()
        if not user:
            print("Default user not found!")
            return
        
        print(f"Testing watchlist addition for user: {user.email} (ID: {user.id})")
        
        # We will try to add a test company: "Reliance Industries" (or "Reliance")
        keyword = "Reliance Industries"
        print(f"Adding keyword: {keyword}")
        
        w = add_watchlist_keyword(
            db,
            keyword=keyword,
            user_id=user.id,
            company_name=keyword,
            exchange="NSE"
        )
        print(f"Watchlist added: ID={w.id}, Keyword={w.keyword}, Company Name={w.company_name}")
        
        print("Running analyze_watchlist_company...")
        analysis = analyze_watchlist_company(db, w.id, user.id, force=True)
        print("Analysis completed successfully!")
        print("Keys in analysis cache:", list(analysis.keys()) if analysis else None)
        
    except Exception as e:
        print("TEST FAILED WITH EXCEPTION:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_test()
