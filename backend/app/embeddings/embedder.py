import logging

logger = logging.getLogger(__name__)

_model = None

def get_model():
    """Lazy-loads the SentenceTransformer model."""
    global _model
    if _model is None:
        try:
            logger.info("Lazy-loading SentenceTransformer model BAAI/bge-small-en-v1.5...")
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            return None
    return _model

def generate_embedding(text: str):
    model = get_model()
    if model is None:
        logger.warning("Using fallback zero-vector embedding (384 dimensions).")
        return [0.0] * 384
    try:
        return model.encode(text).tolist()
    except Exception as e:
        logger.error(f"Error during embedding generation: {e}")
        return [0.0] * 384