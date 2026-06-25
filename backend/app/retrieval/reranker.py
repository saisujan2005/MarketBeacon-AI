from sentence_transformers import CrossEncoder

model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

def rerank(query, documents):
    if not documents:
        return []

    pairs = [
        [query, doc.get("text", doc["title"])[:500]]  # limit length slightly for speed
        for doc in documents
    ]

    scores = model.predict(pairs)

    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    ranked = sorted(
        documents,
        key=lambda x: x.get("rerank_score", 0.0),
        reverse=True
    )

    return ranked