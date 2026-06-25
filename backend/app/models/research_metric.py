import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ResearchMetric(Base):
    __tablename__ = "research_metrics"

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

    session_id = Column(
        String(255),
        nullable=True,
        index=True
    )

    query = Column(
        Text,
        nullable=False
    )

    retrieved_count = Column(
        Integer,
        default=0
    )

    reranked_count = Column(
        Integer,
        default=0
    )

    sources_used = Column(
        JSON,
        nullable=True
    )

    latency_ms = Column(
        Float,
        default=0.0
    )

    token_estimate = Column(
        Integer,
        default=0
    )

    retrieval_quality = Column(
        Float,
        default=0.0
    )

    confidence_score = Column(
        Float,
        default=0.0
    )

    citation_coverage = Column(
        Float,
        default=0.0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    user = relationship("User", back_populates="research_metrics")
