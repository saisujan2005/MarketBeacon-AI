from app.db.database import SessionLocal
from app.models.post import Post
from app.embeddings.qdrant_service import create_collection

from app.embeddings.indexing_service import (
    index_article
)

create_collection()
from app.embeddings.qdrant_service import client

print(client.get_collections())

db = SessionLocal()

posts = db.query(Post).all()

for post in posts:
    index_article(post)

print(f"Indexed {len(posts)} posts")