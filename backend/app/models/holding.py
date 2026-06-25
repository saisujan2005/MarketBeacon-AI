from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class Holding(Base):
    __tablename__ = "holdings"

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
        String,
        nullable=False
    )

    exchange = Column(
        String,
        nullable=True
    )

    quantity = Column(
        Float,
        nullable=False,
        default=0.0
    )

    average_buy_price = Column(
        Float,
        nullable=False,
        default=0.0
    )

    current_price = Column(
        Float,
        nullable=True
    )

    investment_date = Column(
        DateTime,
        default=datetime.utcnow
    )

    notes = Column(
        String,
        nullable=True
    )

    tags = Column(
        JSON,
        nullable=True,
        default=list
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = relationship("User", backref="holdings")
