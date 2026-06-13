from app.db.database import SessionLocal
from app.models.post import Post
from app.retrieval.bm25_service import BM25Retriever
from app.embeddings.search_service import search_news
from app.retrieval.reranker import rerank


def hybrid_search(query, top_k=5):

    db = SessionLocal()

    posts = db.query(Post).all()

    documents = []
    post_lookup = {}

    for post in posts:

        documents.append(post.title)

        post_lookup[post.title] = {
            "title": post.title,
            "url": post.post_url
        }

    bm25 = BM25Retriever(documents)

    bm25_results = bm25.search(
        query,
        top_k=10
    )

    vector_results = search_news(query)

    combined = []

    # BM25 results
    for doc, score in bm25_results:

        combined.append({
            "title": doc,
            "url": post_lookup[doc]["url"],
            "score": float(score)
        })

    # Vector results
    for result in vector_results:

        combined.append({
            "title": result.payload["title"],
            "url": result.payload["url"],
            "score": float(result.score)
        })

    # Deduplicate by title
    unique = {}

    for item in combined:

        title = item["title"]

        if title not in unique:
            unique[title] = item

        else:
            # Keep higher score if duplicate exists
            if item["score"] > unique[title]["score"]:
                unique[title] = item

    combined = list(unique.values())

    
    reranked = rerank(
          query,
          combined
)

    return reranked[:top_k]