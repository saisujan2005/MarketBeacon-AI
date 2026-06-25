from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

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
        nullable=True
    )

    company_name = Column(
        String,
        nullable=True
    )

    exchange = Column(
        String,
        nullable=True
    )

    sector = Column(
        String,
        nullable=True
    )

    industry = Column(
        String,
        nullable=True
    )

    notes = Column(
        String,
        nullable=True
    )

    favorite = Column(
        Boolean,
        default=False
    )

    priority = Column(
        Integer,
        default=3
    )

    added_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    last_analyzed_at = Column(
        DateTime,
        nullable=True
    )

    analysis_cache = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship("User", back_populates="watchlists")