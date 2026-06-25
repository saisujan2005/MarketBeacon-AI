from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.research_report import ResearchReport
from app.agents.research_report_agent import generate_research_report

router = APIRouter()


@router.post("/research-reports/generate")
def generate_report(data: dict, db: Session = Depends(get_db)):
    """
    Triggers synthesis of a new multi-agent research report for a target entity.
    """
    entity = data.get("entity", "").strip()
    if not entity:
        raise HTTPException(status_code=400, detail="Entity name is required.")

    report = generate_research_report(db, entity)
    return {
        "message": f"Report generated successfully for {entity}",
        "report": {
            "id": str(report.id),
            "entity_name": report.entity_name,
            "created_at": report.created_at.isoformat(),
            "report_data": report.report_data
        }
    }


@router.get("/research-reports")
def get_reports_list(db: Session = Depends(get_db)):
    """
    Returns list of previously generated research reports.
    """
    reports = (
        db.query(ResearchReport)
        .order_by(ResearchReport.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "entity_name": r.entity_name,
            "created_at": r.created_at.isoformat(),
            "rating": r.report_data.get("overall_rating", "NEUTRAL") if isinstance(r.report_data, dict) else "NEUTRAL"
        }
        for r in reports
    ]


@router.get("/research-reports/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full report details for a specific report ID.
    """
    report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Research report not found.")

    return {
        "id": str(report.id),
        "entity_name": report.entity_name,
        "created_at": report.created_at.isoformat(),
        "report_data": report.report_data
    }
