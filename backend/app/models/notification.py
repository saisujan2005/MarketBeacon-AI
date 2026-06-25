from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    keyword = Column(
        String,
        nullable=False
    )

    title = Column(
        String,
        nullable=False
    )

    is_read = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    posted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    fetched_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    source = Column(
        String,
        nullable=True
    )

    sentiment = Column(
        String,
        nullable=True
    )

    event_type = Column(
        String,
        nullable=True
    )

    importance_score = Column(
        Integer,
        nullable=True
    )

    post_url = Column(
        String,
        nullable=True
    )

    meta_info = Column(
        JSON,
        nullable=True
    )

    user = relationship("User", back_populates="notifications")