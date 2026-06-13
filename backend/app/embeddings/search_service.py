from app.embeddings.embedder import generate_embedding
from app.embeddings.qdrant_service import (
    client,
    COLLECTION_NAME
)

def search_news(query: str):

    query_vector = generate_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=5
    )

    return results.points