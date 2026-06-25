from sqlalchemy import Column, String, DateTime, Text, ForeignKey
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
        nullable=False
    )

    title = Column(String)

    event_type = Column(String)

    importance_score = Column(String)

    post_id = Column(
        UUID(as_uuid=True),
        nullable=True
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