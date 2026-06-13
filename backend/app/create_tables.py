from app.db.database import engine
from app.models.base import Base

# Import models
from app.models.source import Source
from app.models.post import Post

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")