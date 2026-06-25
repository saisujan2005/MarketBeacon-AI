import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class CompanyPeerCache(Base):
    __tablename__ = "company_peer_caches"

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

    company_name = Column(
        String(255),
        index=True,
        nullable=False
    )

    sector = Column(
        String(255),
        nullable=True
    )

    industry = Column(
        String(255),
        nullable=True
    )

    market_cap_range = Column(
        String(100),
        nullable=True
    )

    peers = Column(
        JSON,
        nullable=False  # List of company names
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("user_id", "company_name", name="uq_user_company_peer"),
    )


class CompanyResearchCache(Base):
    __tablename__ = "company_research_caches"

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

    company_name = Column(
        String(255),
        index=True,
        nullable=False
    )

    scorecard = Column(
        JSON,
        nullable=False
    )

    timeline = Column(
        JSON,
        nullable=False
    )

    peer_comparison = Column(
        JSON,
        nullable=False
    )

    dossier_text = Column(
        JSON,  # Stores overview, business model, risks, opportunities, investment outlook
        nullable=False
    )

    confidence_score = Column(
        Integer,
        default=80
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    __table_args__ = (
        UniqueConstraint("user_id", "company_name", name="uq_user_company_research"),
    )
