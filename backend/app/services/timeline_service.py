import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.timeline_event import TimelineEvent


def add_timeline_event(
    db: Session,
    entity_name: str,
    entity_type: str,
    post_id: uuid.UUID,
    event_date: datetime,
    event_title: str,
    description: str = ""
) -> TimelineEvent:
    """
    Creates and stores a historical timeline event linked to an entity and a post.
    Checks if a timeline event for this entity and post already exists to prevent duplicates.
    """
    # Prevent duplicate event entries for the same post + entity combination
    if post_id:
        existing = (
            db.query(TimelineEvent)
            .filter(
                TimelineEvent.entity_name == entity_name,
                TimelineEvent.post_id == post_id
            )
            .first()
        )
        if existing:
            return existing

    event = TimelineEvent(
        id=uuid.uuid4(),
        entity_name=entity_name,
        entity_type=entity_type,
        post_id=post_id,
        event_date=event_date,
        event_title=event_title,
        description=description
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_timeline_for_entity(db: Session, entity_name: str):
    """
    Retrieves all timeline events for a given entity ordered chronologically.
    """
    return (
        db.query(TimelineEvent)
        .filter(TimelineEvent.entity_name.ilike(entity_name.strip()))
        .order_by(TimelineEvent.event_date.asc())
        .all()
    )


def get_timeline_entities(db: Session):
    """
    Retrieves a list of all distinct entities that have timeline events stored.
    """
    results = (
        db.query(TimelineEvent.entity_name, TimelineEvent.entity_type)
        .distinct()
        .all()
    )
    return [{"name": r[0], "type": r[1]} for r in results]
