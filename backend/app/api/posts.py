from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.db.dependencies import get_db
from app.models.post import Post
from app.schemas.post import PostResponse
from app.rag.llm_service import ask_llm

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


@router.get("/", response_model=list[PostResponse])
def get_posts(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit

    # Sort news by posted_at DESC (falling back to fetched_at DESC)
    posts = (
        db.query(Post)
        .order_by(func.coalesce(Post.posted_at, Post.fetched_at).desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return posts


@router.post("/{post_id}/summarize")
def summarize_post(post_id: UUID, db: Session = Depends(get_db)):
    """
    Generate an AI-structured explanation of a news article:
    1. What happened
    2. Why it matters
    3. Market impact
    4. Key takeaway
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    prompt = f"""You are a financial analysis assistant. Analyze this financial news article.

Provide an explanation containing exactly these four sections, formatted with these headers:

What happened:
[Provide a clear, one-sentence description of the event]

Why it matters:
[Explain the underlying financial/economic significance in one sentence]

Market impact:
[List the likely immediate sentiment direction for 2-3 relevant assets, sectors, or currencies in bullet points, e.g. • Gold: Bearish]

Key takeaway:
[Provide a one-sentence final conclusion/outlook]

Format the output cleanly. Do not include markdown code block formatting (like ```) or extra conversational text.

News Title: {post.title}
News Content: {post.content or 'No detailed content available.'}
Sentiment: {post.sentiment or 'NEUTRAL'}
Event Type: {post.event_type or 'OTHER'}
"""
    try:
        summary = ask_llm(prompt, article_title=post.title or "Unknown")
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Summarization failed: {e}")