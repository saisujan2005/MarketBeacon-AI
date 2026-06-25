from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class DailyBriefing(Base):
    __tablename__ = "daily_briefings"

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

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    top_events = Column(
        JSON,
        nullable=False
    )

    bullish_sectors = Column(
        JSON,
        nullable=False
    )

    bearish_sectors = Column(
        JSON,
        nullable=False
    )

    market_summary = Column(
        Text,
        nullable=False
    )

    outlook = Column(
        String,
        nullable=False
    )

    user = relationship("User", back_populates="daily_briefings")
