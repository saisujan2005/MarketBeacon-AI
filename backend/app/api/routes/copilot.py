import uuid
import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.dependencies import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.rag.copilot_agent import answer_copilot_question

# Ingestion & search imports
from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct
from app.models.research_document import ResearchDocument
from app.embeddings.qdrant_service import client as qdrant_client, RESEARCH_COLLECTION_NAME
from app.embeddings.embedder import generate_embedding
from app.services.document_parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    chunk_text
)
from app.services.research_agent import get_or_generate_company_research
from app.services.financial_data import normalize_company_name

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Copilot"])


@router.post("/chat/session")
@router.post("/api/chat/session")
def create_session(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Creates a new chat session for the current user.
    """
    session = ChatSession(user_id=current_user.id, title="New Conversation")
    db.add(session)
    db.commit()
    db.refresh(session)
    return {
        "session_id": str(session.id),
        "title": session.title,
        "created_at": session.created_at.isoformat()
    }


@router.get("/chat/sessions")
@router.get("/api/chat/sessions")
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lists all chat sessions for the current user.
    """
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [
        {
            "session_id": str(s.id),
            "title": s.title,
            "created_at": s.created_at.isoformat()
        }
        for s in sessions
    ]


@router.get("/chat/history/{session_id}")
@router.get("/api/chat/history/{session_id}")
def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves full message history of a chat session belonging to the user.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    session = db.query(ChatSession).filter(ChatSession.id == session_uuid, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_uuid)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return {
        "session_id": str(session.id),
        "title": session.title,
        "summary": session.summary,
        "created_at": session.created_at.isoformat(),
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }


@router.post("/chat/message")
@router.post("/api/chat/message")
def post_message(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sends a question, runs RAG, and generates the Copilot assistant response.
    """
    session_id = req.get("session_id")
    question = req.get("question")
    deep_research = req.get("deep_research", False)

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    if not session_id:
        session = ChatSession(user_id=current_user.id, title=question[:40] + "...")
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = str(session.id)
    else:
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session_id format")
        
        session = db.query(ChatSession).filter(ChatSession.id == session_uuid, ChatSession.user_id == current_user.id).first()
        if not session:
            session = ChatSession(id=session_uuid, user_id=current_user.id, title=question[:40] + "...")
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = str(session.id)
        else:
            if session.title == "New Conversation":
                session.title = question[:40] + "..."
                db.commit()

    result = answer_copilot_question(db, session_id, question, current_user.id, deep_research)
    return result


@router.delete("/chat/session/{session_id}")
@router.delete("/api/chat/session/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a conversation session and all its messages.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    session = db.query(ChatSession).filter(ChatSession.id == session_uuid, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    db.delete(session)
    db.commit()
    return {"message": "Chat session deleted successfully"}


@router.post("/research/company")
@router.post("/api/research/company")
def research_company(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint for triggering structured company research dossier directly.
    """
    company_name = req.get("company_name")
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name is required")

    company_name = normalize_company_name(company_name)

    session = ChatSession(user_id=current_user.id, title=f"Research on {company_name}")
    db.add(session)
    db.commit()
    db.refresh(session)

    question = f"Analyze {company_name}"
    result = answer_copilot_question(db, str(session.id), question, current_user.id, deep_research=False)
    return result


@router.post("/research/deep")
@router.post("/api/research/deep")
def research_deep(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint for triggering Deep Research directly.
    """
    query = req.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    session = ChatSession(user_id=current_user.id, title=f"Deep Research: {query[:30]}...")
    db.add(session)
    db.commit()
    db.refresh(session)

    result = answer_copilot_question(db, str(session.id), query, current_user.id, deep_research=True)
    return result


# ── Research Library Endpoints ───────────────────────────────────────────────

@router.post("/research/upload")
@router.post("/api/research/upload")
def upload_research_document(
    file: UploadFile = File(...),
    company_name: Optional[str] = Form(None),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingests PDF, DOCX, or TXT documents, chunks them, computes embeddings,
    indexes them in Qdrant, and saves metadata in PostgreSQL under the authenticated user.
    """
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension {ext}. Supported types: PDF, DOCX, TXT."
        )

    doc = ResearchDocument(
        user_id=current_user.id,
        title=filename,
        company_name=company_name,
        document_type=document_type,
        status="Processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    logger.info(f"[Ingestion] Document metadata entry created: ID {doc.id} (User: {current_user.id})")

    try:
        uploads_dir = os.path.abspath("d:/MarketBeacon-AI/backend/uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, f"{doc.id}_{filename}")

        file_bytes = file.file.read()
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        doc.file_path = file_path
        db.commit()

        if ext == ".pdf":
            text = extract_text_from_pdf(file_bytes)
        elif ext == ".docx":
            text = extract_text_from_docx(file_bytes)
        else:
            text = extract_text_from_txt(file_bytes)

        if not text.strip():
            raise ValueError("No text content could be extracted from this document.")

        chunks = chunk_text(text, chunk_size_tokens=900, overlap_tokens=120)
        doc.chunk_count = len(chunks)
        db.commit()

        logger.info(f"[Ingestion] Generated {len(chunks)} chunks for {filename}")

        # Embed & Index chunks in Qdrant with user_id!
        points = []
        for idx, chunk in enumerate(chunks):
            embedding = generate_embedding(chunk)
            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "user_id": str(current_user.id),  # Store user_id inside Qdrant chunk
                    "document_id": str(doc.id),
                    "company_name": company_name or "",
                    "document_type": document_type,
                    "source_file": filename,
                    "chunk_index": idx,
                    "upload_date": doc.upload_date.isoformat() + "Z",
                    "text": chunk
                }
            )
            points.append(point)

        if points:
            qdrant_client.upsert(
                collection_name=RESEARCH_COLLECTION_NAME,
                points=points
            )

        doc.status = "Indexed"
        db.commit()
        logger.info(f"[Ingestion] Document ID {doc.id} successfully Indexed (User: {current_user.id})")

        return {
            "message": "File indexed successfully",
            "document_id": str(doc.id),
            "title": doc.title,
            "company_name": doc.company_name,
            "document_type": doc.document_type,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "indexing_stats": {
                "total_bytes": len(file_bytes),
                "extracted_characters": len(text),
                "total_chunks": len(chunks)
            }
        }

    except Exception as e:
        logger.error(f"[Ingestion] Failed to ingest document ID {doc.id}: {e}")
        doc.status = "Failed"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get("/research/documents")
@router.get("/api/research/documents")
def get_research_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns list of all uploaded research document records for this user.
    """
    docs = (
        db.query(ResearchDocument)
        .filter(ResearchDocument.user_id == current_user.id)
        .order_by(ResearchDocument.upload_date.desc())
        .all()
    )
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "company_name": d.company_name,
            "document_type": d.document_type,
            "upload_date": d.upload_date.isoformat(),
            "chunk_count": d.chunk_count,
            "status": d.status,
            "file_path": d.file_path
        }
        for d in docs
    ]


@router.delete("/research/document/{document_id}")
@router.delete("/api/research/document/{document_id}")
def delete_research_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes research document metadata, chunks from Qdrant, and local file.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id format")

    doc = db.query(ResearchDocument).filter(ResearchDocument.id == doc_uuid, ResearchDocument.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Delete chunks from Qdrant
    try:
        qdrant_client.delete(
            collection_name=RESEARCH_COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=str(doc.id))
                    )
                ]
            )
        )
        logger.info(f"[Deletion] Chunks for document ID {doc.id} removed from Qdrant")
    except Exception as e:
        logger.error(f"[Deletion] Failed to delete chunks from Qdrant: {e}")

    # 2. Delete local file
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
            logger.info(f"[Deletion] Local file deleted: {doc.file_path}")
        except Exception as e:
            logger.error(f"[Deletion] Failed to delete local file: {e}")

    # 3. Delete database record
    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.title}' deleted successfully"}


@router.post("/research/search")
@router.post("/api/research/search")
def search_research_library(
    req: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Searches the user's uploaded research document chunks in Qdrant.
    """
    query = req.get("query")
    company_name = req.get("company_name")
    document_type = req.get("document_type")
    top_k = req.get("top_k", 5)

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")

    must_filters = [
        FieldCondition(
            key="user_id",
            match=MatchValue(value=str(current_user.id))
        )
    ]
    if company_name and company_name != "all":
        must_filters.append(
            FieldCondition(
                key="company_name",
                match=MatchValue(value=company_name)
            )
        )
    if document_type and document_type != "all":
        must_filters.append(
            FieldCondition(
                key="document_type",
                match=MatchValue(value=document_type)
            )
        )

    query_filter = Filter(must=must_filters)

    try:
        embedding = generate_embedding(query)
        search_results = qdrant_client.search(
            collection_name=RESEARCH_COLLECTION_NAME,
            query_vector=embedding,
            query_filter=query_filter,
            limit=top_k
        )

        output = []
        for r in search_results:
            output.append({
                "document_id": r.payload.get("document_id"),
                "company_name": r.payload.get("company_name"),
                "document_type": r.payload.get("document_type"),
                "source_file": r.payload.get("source_file"),
                "chunk_index": r.payload.get("chunk_index"),
                "text": r.payload.get("text"),
                "score": r.score
            })
        return output
    except Exception as e:
        logger.error(f"[Search] Failed to query Qdrant collection: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/research/evaluate")
@router.post("/api/research/evaluate")
def evaluate_research(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns retrieval quality and latency metrics for this user.
    """
    query_str = req.get("query")
    from app.models.research_metric import ResearchMetric

    q = db.query(ResearchMetric).filter(ResearchMetric.user_id == current_user.id)
    if query_str:
        metric = q.filter(ResearchMetric.query.ilike(f"%{query_str}%")).order_by(ResearchMetric.created_at.desc()).first()
    else:
        metric = q.order_by(ResearchMetric.created_at.desc()).first()

    if not metric:
        return {
            "retrieval_quality": 0.85,
            "source_count": 5,
            "confidence": 85.0,
            "latency": 320.0,
            "message": "No logged queries found in database. Showing baseline estimation."
        }

    return {
        "retrieval_quality": float(metric.retrieval_quality),
        "source_count": int(metric.retrieved_count),
        "confidence": float(metric.confidence_score),
        "latency": float(metric.latency_ms),
        "query": metric.query,
        "logged_at": metric.created_at.isoformat()
    }


@router.get("/research/metrics/aggregate")
@router.get("/api/research/metrics/aggregate")
def get_aggregate_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns aggregated RAG evaluation performance statistics and recent query logs for this user.
    """
    from app.models.research_metric import ResearchMetric
    from sqlalchemy import func

    # Filter stats by authenticated user
    stats = db.query(
        func.avg(ResearchMetric.latency_ms).label("avg_latency"),
        func.avg(ResearchMetric.confidence_score).label("avg_confidence"),
        func.avg(ResearchMetric.retrieved_count).label("avg_source_count"),
        func.avg(ResearchMetric.citation_coverage).label("avg_citation_coverage"),
        func.avg(ResearchMetric.retrieval_quality).label("avg_retrieval_quality"),
        func.count(ResearchMetric.id).label("total_queries")
    ).filter(ResearchMetric.user_id == current_user.id).first()

    recent_records = (
        db.query(ResearchMetric)
        .filter(ResearchMetric.user_id == current_user.id)
        .order_by(ResearchMetric.created_at.desc())
        .limit(20)
        .all()
    )

    recent_queries = [
        {
            "id": str(r.id),
            "query": r.query,
            "latency": float(round(r.latency_ms, 2)),
            "confidence": float(round(r.confidence_score, 2)),
            "source_count": int(r.retrieved_count),
            "citation_coverage": float(round(r.citation_coverage, 2)),
            "retrieval_quality": float(round(r.retrieval_quality, 2)),
            "logged_at": r.created_at.isoformat()
        }
        for r in recent_records
    ]

    return {
        "avg_latency": float(round(stats.avg_latency or 350.0, 2)),
        "avg_confidence": float(round(stats.avg_confidence or 85.0, 2)),
        "avg_source_count": float(round(stats.avg_source_count or 5.0, 2)),
        "avg_citation_coverage": float(round(stats.avg_citation_coverage or 0.8, 2)),
        "avg_retrieval_quality": float(round(stats.avg_retrieval_quality or 0.85, 2)),
        "total_queries": int(stats.total_queries or 0),
        "recent_queries": recent_queries
    }


@router.post("/research/scorecard")
@router.post("/api/research/scorecard")
def get_scorecard(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_name = req.get("company_name")
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name is required")
    try:
        data = get_or_generate_company_research(db, company_name, user_id=current_user.id)
        return {
            "company_name": data.get("company_name"),
            "scorecard": data.get("scorecard"),
            "confidence_score": data.get("confidence_score")
        }
    except Exception as e:
        logger.error(f"Error in /research/scorecard for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/timeline")
@router.post("/api/research/timeline")
def get_timeline(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_name = req.get("company_name")
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name is required")
    try:
        data = get_or_generate_company_research(db, company_name, user_id=current_user.id)
        return {
            "company_name": data.get("company_name"),
            "timeline": data.get("timeline"),
            "confidence_score": data.get("confidence_score")
        }
    except Exception as e:
        logger.error(f"Error in /research/timeline for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/peers")
@router.post("/api/research/peers")
def get_peers(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_name = req.get("company_name")
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name is required")
    try:
        data = get_or_generate_company_research(db, company_name, user_id=current_user.id)
        return {
            "company_name": data.get("company_name"),
            "peer_comparison": data.get("peer_comparison"),
            "confidence_score": data.get("confidence_score")
        }
    except Exception as e:
        logger.error(f"Error in /research/peers for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/dossier")
@router.post("/api/research/dossier")
def get_dossier(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_name = req.get("company_name")
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name is required")
    try:
        data = get_or_generate_company_research(db, company_name, user_id=current_user.id)
        return data
    except Exception as e:
        logger.error(f"Error in /research/dossier for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
