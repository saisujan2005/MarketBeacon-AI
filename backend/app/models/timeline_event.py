from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.models.base import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    entity_name = Column(
        String,
        index=True,
        nullable=False
    )

    entity_type = Column(
        String,
        nullable=False
    )

    post_id = Column(
        UUID(as_uuid=True),
        nullable=True
    )

    event_date = Column(
        DateTime,
        nullable=False
    )

    event_title = Column(
        String,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
