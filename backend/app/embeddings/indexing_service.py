from qdrant_client.models import PointStruct

from app.embeddings.embedder import generate_embedding
from app.embeddings.qdrant_service import (
    client,
    COLLECTION_NAME
)

def index_article(post):

    text = f"{post.title}"

    embedding = generate_embedding(text)

    point = PointStruct(
        id=str(post.id),
        vector=embedding,
        payload={
            "title": post.title,
            "url": post.post_url
        }
    )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point]
    )