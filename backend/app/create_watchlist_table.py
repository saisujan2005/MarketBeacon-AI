from app.models.base import Base
from app.models.watchlist import Watchlist
from app.db.database import engine

Base.metadata.create_all(bind=engine)

print("Watchlist table created")