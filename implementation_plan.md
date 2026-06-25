# Implementation Plan - Thread-Safe Singleton Qdrant Client Integration

This plan details the implementation steps to replace the eagerly initialized global Qdrant client with a thread-safe, lazy singleton client featuring robust startup/shutdown lifecycle hooks, lock collision diagnostics, and verification.

## Proposed Changes

### Backend Components

---

#### [MODIFY] [qdrant_service.py](file:///d:/MarketBeacon-AI/backend/app/embeddings/qdrant_service.py)
- Replace direct module-level instantiation with a thread-safe, lazy singleton implementation:
  - Add a threading Lock to serialize initialization.
  - Implement `get_qdrant_client()` which lazily instantiates the single shared `QdrantClient` in a thread-safe manner.
  - Export a `client` variable bound to a lazy wrapper `QdrantClientProxy` to preserve backward compatibility for all existing imports.
- Implement detailed lock detection:
  - Catch directory access errors (such as `RuntimeError` regarding locking) and raise a user-friendly `RuntimeError` detailing:
    - Diagnostic info (local database is locked).
    - Recommended recovery steps (kill stale python/uvicorn processes, delete `.lock` file, check for background schedulers).
- Implement collection check and initialization:
  - Implement `init_collections(client)` to dynamically verify and automatically build the `market_news` and `research_documents` collections.
- Implement graceful closing:
  - Implement `close_qdrant_client()` to safely close and release file handles.

#### [MODIFY] [main.py](file:///d:/MarketBeacon-AI/backend/app/main.py)
- Update the FastAPI `lifespan` handler:
  - On startup: Retrieve the shared client (`get_qdrant_client()`), call collection initialization, and log a clear success message.
  - On shutdown: Call `close_qdrant_client()` to release file locks before Uvicorn exits.

---

## Verification Plan

### Automated Tests
- Run `backend/app/test_qdrant.py` or a custom python script to confirm the thread-safe proxy behaves identical to direct instantiation and queries collections successfully.

### Manual Verification
1. Boot the application with `uvicorn app.main:app` and verify startup logs show collections verified and client successfully registered.
2. Confirm pages (Portfolio, Research Workspace, Copilot, Alerts) load and run vector search/ingestion correctly.
3. Test concurrent requests to verify thread-safe initialization does not create duplicate clients.
4. Restart the server multiple times to verify locks are cleanly released.
