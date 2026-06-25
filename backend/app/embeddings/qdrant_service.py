import logging
import os
import threading
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logger = logging.getLogger(__name__)

COLLECTION_NAME = "market_news"
RESEARCH_COLLECTION_NAME = "research_documents"

# Resolve absolute path to backend/qdrant_data consistently
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
QDRANT_PATH = os.path.join(BASE_DIR, "qdrant_data")

logger.info(f"Qdrant database path resolved to: {QDRANT_PATH}")

_client = None
_lock = threading.Lock()

def get_qdrant_client() -> QdrantClient:
    """
    Thread-safe lazy singleton client getter.
    """
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                try:
                    logger.info(f"Initializing shared QdrantClient instance (path='{QDRANT_PATH}')...")
                    _client = QdrantClient(path=QDRANT_PATH)
                except Exception as e:
                    err_str = str(e)
                    if "already accessed by another instance" in err_str or "lock" in err_str.lower():
                        msg = (
                            "\n" + "="*80 + "\n"
                            "CRITICAL ERROR: Local Qdrant database folder is locked!\n\n"
                            f"Path: {QDRANT_PATH}\n\n"
                            "Diagnostic: Another process (such as a news scheduler, database script, or another\n"
                            "Uvicorn worker process) is already holding the lock on the Qdrant database files.\n\n"
                            "Recommended Recovery Steps:\n"
                            "1. Locate and terminate duplicate processes: run 'taskkill /F /IM python.exe' in Windows.\n"
                            "2. Check for background RSS news schedulers or ingestion scripts that might be running.\n"
                            "3. If no python processes are active, clean up any stale lock files manually:\n"
                            "   Delete the '.lock' file in the directory 'backend/qdrant_data/'.\n"
                            "4. Restart the application.\n" +
                            "="*80 + "\n"
                        )
                        logger.error(msg)
                        raise RuntimeError(
                            "Local Qdrant database is already locked. Please stop other active instances "
                            f"and delete the '.lock' file in {QDRANT_PATH} if stale."
                        ) from None
                    raise e
    return _client

def close_qdrant_client():
    """
    Gracefully closes and cleans up the active client connection.
    """
    global _client
    if _client is not None:
        with _lock:
            if _client is not None:
                try:
                    logger.info("Closing QdrantClient singleton database handles...")
                    _client.close()
                except Exception as e:
                    logger.error(f"Failed to close QdrantClient: {e}")
                finally:
                    _client = None

class QdrantClientProxy:
    """
    Proxy pattern delegating all attributes and operations to the thread-safe singleton.
    """
    def __getattr__(self, name):
        return getattr(get_qdrant_client(), name)
        
    def __repr__(self):
        return f"<QdrantClientProxy (Target: {hex(id(_client)) if _client else 'None'})>"

# Export the proxy client to maintain backward compatibility with all imports
client = QdrantClientProxy()

def create_collection():
    """
    Verifies that the required collections exist, creating them if necessary.
    Uses the thread-safe proxy client.
    """
    logger.info("Verifying Qdrant collections...")
    collections = client.get_collections()

    existing = [
        c.name
        for c in collections.collections
    ]

    if COLLECTION_NAME not in existing:
        logger.info(f"Creating collection '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
    else:
        logger.info(f"Collection '{COLLECTION_NAME}' already exists.")

    if RESEARCH_COLLECTION_NAME not in existing:
        logger.info(f"Creating collection '{RESEARCH_COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=RESEARCH_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
    else:
        logger.info(f"Collection '{RESEARCH_COLLECTION_NAME}' already exists.")