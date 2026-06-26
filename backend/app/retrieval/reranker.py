import os

logger = logging.getLogger(__name__)

DISABLE_LOCAL_ML = os.getenv("DISABLE_LOCAL_ML", "False").lower() in ("true", "1", "yes")

_model = None

def get_model():
    """Lazy-loads the CrossEncoder reranker model."""
    global _model
    if DISABLE_LOCAL_ML:
        return None
    if _model is None:
        try:
            logger.info("Lazy-loading CrossEncoder model cross-encoder/ms-marco-MiniLM-L-6-v2...")
            from sentence_transformers import CrossEncoder
            _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("CrossEncoder model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder model: {e}")
            return None
    return _model

def rerank(query, documents):
    if not documents:
        return []

    model = get_model()
    if model is None:
        logger.warning("Skipping reranking step due to missing model (fallback to original order).")
        # Ensure rerank_score is populated to avoid frontend or service errors
        for doc in documents:
            if "rerank_score" not in doc:
                # Use default score or importance score as fallback
                doc["rerank_score"] = float(doc.get("score", doc.get("importance_score", 0.0)))
        return documents

    try:
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
    except Exception as e:
        logger.error(f"Error during reranking: {e}. Falling back to original order.")
        for doc in documents:
            if "rerank_score" not in doc:
                doc["rerank_score"] = float(doc.get("score", doc.get("importance_score", 0.0)))
        return documents
