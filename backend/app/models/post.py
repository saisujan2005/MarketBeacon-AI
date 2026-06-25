from sqlalchemy import Column, String, Text, DateTime, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.models.base import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Plain string — no foreign key needed for RSS sources like "ndtv_profit"
    source_id = Column(
        String,
        nullable=True
    )

    external_id = Column(
        String,
        unique=True,
        nullable=False
    )

    title = Column(String)

    content = Column(Text)

    post_url = Column(String)

    posted_at = Column(DateTime)

    fetched_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    event_type = Column(
        String,
        nullable=True
    )

    importance_score = Column(
        Integer,
        nullable=True
    )

    impact_level = Column(
        String,
        nullable=True
    )

    reasoning = Column(
        Text,
        nullable=True
    )

    confidence = Column(
        Integer,
        nullable=True
    )

    affected_assets = Column(
        JSON,
        nullable=True
    )

    sentiment = Column(
        String,
        nullable=True
    )

    sentiment_confidence = Column(
        Float,
        nullable=True
    )

    sentiment_reasoning = Column(
        Text,
        nullable=True
    )

    entities = Column(
        JSON,
        nullable=True
    )

    predicted_direction = Column(
        String,
        nullable=True
    )

    prediction_confidence = Column(
        Float,
        nullable=True
    )

    prediction_reasoning = Column(
        Text,
        nullable=True
    )