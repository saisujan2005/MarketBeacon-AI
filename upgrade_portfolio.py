import sys
import os

# Adjust path to include the backend folder
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.db.database import engine
from app.models.base import Base
from app.models.holding import Holding  # noqa: F401
from app.models.user import User  # noqa: F401

def main():
    print("Running migration to create 'holdings' table...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database schema upgraded successfully. Table 'holdings' created.")
    except Exception as e:
        print(f"Error executing migration: {e}")

if __name__ == "__main__":
    main()
