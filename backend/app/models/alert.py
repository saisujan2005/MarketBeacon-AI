from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title = Column(String)

    event_type = Column(String)

    # Numeric. Previously String, which made `importance_score >= 80` a
    # lexicographic comparison in Postgres: '100' sorted below '80' (so the most
    # critical alerts were excluded) while '9' sorted above it.
    importance_score = Column(Integer, nullable=True)

    post_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    post_url = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    summary_text = Column(Text, nullable=True)

    summary_generated_at = Column(
        DateTime,
        nullable=True
    )

    user = relationship("User", back_populates="alerts")

    __table_args__ = (
        # Alert feeds are always "this user's alerts, newest first".
        Index("ix_alerts_user_created", "user_id", "created_at"),
        # Duplicate suppression looks up (user_id, post_id) and (user_id, title).
        Index("ix_alerts_user_post", "user_id", "post_id"),
    )
