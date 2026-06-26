from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.timeline_service import (
    get_timeline_for_entity,
    get_timeline_entities,
    generate_timeline_summary
)

router = APIRouter()


@router.get("/timeline/entities")
def get_entities(db: Session = Depends(get_db)):
    """
    Returns list of all unique entities that have timeline events.
    """
    return get_timeline_entities(db)


@router.get("/timeline/{entity_name}")
def get_timeline(entity_name: str, db: Session = Depends(get_db)):
    """
    Returns the chronological timeline of events for a given entity.
    """
    events = get_timeline_for_entity(db, entity_name)
    return [
        {
            "id": str(e.id),
            "entity_name": e.entity_name,
            "entity_type": e.entity_type,
            "post_id": str(e.post_id) if e.post_id else None,
            "event_date": e.event_date.isoformat(),
            "event_title": e.event_title,
            "description": e.description
        }
        for e in events
    ]


@router.post("/timeline/{entity_name}/summary")
@router.post("/api/timeline/{entity_name}/summary")
def get_entity_timeline_summary(entity_name: str, db: Session = Depends(get_db)):
    """
    Generates an AI summary of the timeline events for the given entity.
    """
    summary = generate_timeline_summary(db, entity_name)
    return {"summary": summary}
