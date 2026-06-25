from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.db.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.research_workspace import ResearchWorkspace
from app.services.workspace_service import generate_research_workspace_data

router = APIRouter(tags=["AI Research Workspace"])


@router.post("/research/workspace/analyze")
@router.post("/api/research/workspace/analyze")
def post_analyze_research_workspace(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query parameter is required.")
    try:
        data = generate_research_workspace_data(db, query, current_user.id)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Research workspace compilation failed: {str(e)}"
        )


@router.get("/research/workspaces")
@router.get("/api/research/workspaces")
def get_user_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        workspaces = db.query(ResearchWorkspace).filter(
            ResearchWorkspace.user_id == current_user.id
        ).order_by(ResearchWorkspace.updated_at.desc()).all()
        return workspaces
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch saved workspaces: {str(e)}"
        )


@router.post("/research/workspace")
@router.post("/api/research/workspace")
def save_research_workspace(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    title = payload.get("title")
    query = payload.get("query")
    analysis_json = payload.get("analysis_json", {})
    notes = payload.get("notes", "")
    is_favorite = payload.get("is_favorite", False)

    if not title or not query:
        raise HTTPException(status_code=400, detail="title and query parameters are required.")

    try:
        workspace = ResearchWorkspace(
            user_id=current_user.id,
            title=title,
            query=query,
            analysis_json=analysis_json,
            notes=notes,
            is_favorite=is_favorite
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        return workspace
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save research workspace: {str(e)}"
        )


@router.put("/research/workspace/{workspace_id}")
@router.put("/api/research/workspace/{workspace_id}")
def update_research_workspace(
    workspace_id: uuid.UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = db.query(ResearchWorkspace).filter(
        ResearchWorkspace.id == workspace_id,
        ResearchWorkspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    if "title" in payload:
        workspace.title = payload["title"]
    if "notes" in payload:
        workspace.notes = payload["notes"]
    if "is_favorite" in payload:
        workspace.is_favorite = payload["is_favorite"]
    if "analysis_json" in payload:
        workspace.analysis_json = payload["analysis_json"]

    workspace.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(workspace)
        return workspace
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update research workspace: {str(e)}"
        )


@router.delete("/research/workspace/{workspace_id}")
@router.delete("/api/research/workspace/{workspace_id}")
def delete_research_workspace(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = db.query(ResearchWorkspace).filter(
        ResearchWorkspace.id == workspace_id,
        ResearchWorkspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    try:
        db.delete(workspace)
        db.commit()
        return {"status": "success", "message": "Workspace deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete research workspace: {str(e)}"
        )


@router.post("/research/workspace/{workspace_id}/duplicate")
@router.post("/api/research/workspace/{workspace_id}/duplicate")
def duplicate_research_workspace(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    src = db.query(ResearchWorkspace).filter(
        ResearchWorkspace.id == workspace_id,
        ResearchWorkspace.user_id == current_user.id
    ).first()

    if not src:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    try:
        dup = ResearchWorkspace(
            user_id=current_user.id,
            title=f"Copy of {src.title}",
            query=src.query,
            analysis_json=src.analysis_json,
            notes=src.notes,
            is_favorite=src.is_favorite
        )
        db.add(dup)
        db.commit()
        db.refresh(dup)
        return dup
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to duplicate workspace: {str(e)}"
        )


@router.post("/research/workspace/export")
@router.post("/api/research/workspace/export")
def export_research_workspace(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assembles a premium Markdown report payload representing the workspace canvas details,
    notes, timeline, and sources for export download.
    """
    title = payload.get("title", "MarketBeacon AI Research report")
    query = payload.get("query", "")
    summary = payload.get("summary", "")
    key_insights = payload.get("key_insights", [])
    risks = payload.get("risks", [])
    opportunities = payload.get("opportunities", [])
    notes = payload.get("notes", "")
    sources = payload.get("sources", [])
    timeline = payload.get("timeline", [])

    md = f"""# MARKETBEACON INSTITUTIONAL RESEARCH REPORT: {title.upper()}
**Query catalyst**: {query}
**Compiled Date**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

## 1. Executive Summary
{summary or "No executive summary parsed."}

## 2. Key Analytical Insights
"""
    for idx, insight in enumerate(key_insights):
        md += f"- **Insight {idx+1}**: {insight}\n"

    md += "\n## 3. Risks & Opportunities\n"
    md += "### Key Identified Risks:\n"
    for r in risks:
        md += f"- ⚠️ {r}\n"
    md += "\n### Key Identified Opportunities:\n"
    for o in opportunities:
        md += f"- 💡 {o}\n"

    md += "\n## 4. Chronological timeline\n"
    for ev in timeline:
        md += f"- **{ev.get('date', '')}** [{ev.get('type', '')}]: {ev.get('title', '')} ({ev.get('badge', '')})\n"
    if not timeline:
        md += "No event timelines compiled.\n"

    md += "\n## 5. Personal Analyst Notes\n"
    md += f"{notes or 'No custom notes logged.'}\n"

    md += "\n## 6. Mapped Evidence Sources & Transparency Index\n"
    for s in sources:
        md += f"- **{s.get('source', '')}** ({s.get('doc_type', '')}) - Date: {s.get('date', '')} | Reliability: {s.get('tier', '')} | Confidence: {s.get('confidence', '')}\n"

    md += "\n---\n*Disclaimer: MarketBeacon research payloads are compiled for research purposes only. Avoid trade recommendations.*"

    return {"status": "success", "markdown": md}
