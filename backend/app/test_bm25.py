from app.db.database import SessionLocal
from app.models.post import Post
from app.embeddings.search_service import search_news

from app.retrieval.bm25_service import (
    BM25Retriever
)

db = SessionLocal()

posts = db.query(Post).all()

documents = [
    post.title
    for post in posts
]

retriever = BM25Retriever(
    documents
)



results = retriever.search("oil prices")

print(results)

results = search_news("oil prices")

print(results)