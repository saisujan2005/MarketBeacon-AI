from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class ResearchReport(Base):
    """
    An AI-generated research report.

    Reports are PRIVATE to the user who generated them. They are surfaced in that
    user's RAG context, so a missing owner column previously meant one user's
    research became retrieval context for every other user.
    """

    __tablename__ = "research_reports"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,   # nullable so pre-existing rows remain loadable
        index=True
    )

    entity_name = Column(
        String,
        index=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    report_data = Column(
        JSON,
        nullable=False
    )

    user = relationship("User", backref="research_reports")

    __table_args__ = (
        # Cache lookups are always "this user's most recent report for entity X".
        Index("ix_research_reports_user_entity_created", "user_id", "entity_name", "created_at"),
    )
