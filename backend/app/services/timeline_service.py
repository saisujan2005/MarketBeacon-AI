import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.timeline_event import TimelineEvent
from app.rag.llm_service import ask_llm


def is_valid_entity_name(name: str) -> bool:
    """
    Validates whether an extracted entity name is clean and meaningful.
    Filters out raw HTML, extremely long strings, and binary/hash codes.
    """
    if not name:
        return False
    name_strip = name.strip()
    
    # 1. Length check: Must be between 2 and 40 characters
    if len(name_strip) < 2 or len(name_strip) > 40:
        return False
        
    # 2. HTML and URL check: Filter out common web remnants
    if any(token in name_strip.lower() for token in ["<", ">", "=", "href", "target=", "http", "www", "_blank"]):
        return False
        
    # 3. Hash/Base64/Token check: Filter out single continuous long alphanumeric strings
    if " " not in name_strip and len(name_strip) > 15:
        return False
        
    # 4. Mostly numbers check: Filter out serial keys or numeric codes
    if len(name_strip) > 12 and name_strip.isalnum() and not name_strip.isalpha():
        return False
        
    return True


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
    Retrieves a list of all distinct entities that have timeline events stored,
    filtering out long or corrupted entries.
    """
    results = (
        db.query(TimelineEvent.entity_name, TimelineEvent.entity_type)
        .distinct()
        .all()
    )
    filtered = []
    for r in results:
        name, etype = r[0], r[1]
        if is_valid_entity_name(name):
            filtered.append({"name": name, "type": etype})
    return filtered


def generate_timeline_summary(db: Session, entity_name: str) -> str:
    """
    Gathers timeline events for a given entity and queries Groq/LLM
    to compile a clean executive briefing of the timeline.
    """
    events = get_timeline_for_entity(db, entity_name)
    if not events:
        return "No timeline events available for this entity."

    events_text = "\n".join([
        f"- Date: {e.event_date.strftime('%d %b %Y') if e.event_date else 'Unknown'} | Title: {e.event_title} | Description: {e.description or ''}"
        for e in events
    ])

    prompt = f"""You are a professional Bloomberg-style financial research analyst.
Analyze the following historical event timeline for the entity "{entity_name}":

{events_text}

Generate a concise, high-impact executive summary (2-3 sentences) explaining the key developments, trends, and overall market implications of these events for "{entity_name}". Do not use bullet points or markdown syntax wrappers; return a single clean paragraph.
"""
    try:
        response = ask_llm(prompt, article_title=f"Timeline Summary: {entity_name}")
        return response.strip()
    except Exception as e:
        return f"Failed to generate AI timeline summary: {str(e)}"
