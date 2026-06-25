from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.timeline_service import get_timeline_for_entity, get_timeline_entities

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
