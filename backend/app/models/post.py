from sqlalchemy import Column, String, Text, DateTime, Integer, Float, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.models.base import Base


class Post(Base):
    """
    An ingested news article plus its enrichment metadata.

    This is the largest and hottest table in the schema, so the indexes below are
    driven by the actual query patterns in the codebase (see __table_args__).
    """

    __tablename__ = "posts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Plain string — no foreign key needed for RSS sources like "ndtv_profit"
    source_id = Column(
        String,
        nullable=True,
        index=True          # filtered by source in the alerts/news feeds
    )

    external_id = Column(
        String,
        unique=True,        # already backed by a unique index (dedup by URL)
        nullable=False
    )

    title = Column(String, index=True)   # Alert.title == Post.title outer join

    content = Column(Text)

    post_url = Column(String, index=True)  # find_matching_post() lookup

    posted_at = Column(DateTime, index=True)   # primary ordering column

    fetched_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    event_type = Column(
        String,
        nullable=True,
        index=True          # /trends group-by and event filters
    )

    importance_score = Column(
        Integer,
        nullable=True,
        index=True          # "IS NULL" enrichment queue scan + ">= 70" feeds
    )

    # Marks that this post has already been through alert generation. Lets the
    # alert pipeline process only new posts instead of rescanning all history.
    alerts_processed_at = Column(
        DateTime,
        nullable=True,
        index=True
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

    __table_args__ = (
        # /market-summary: WHERE importance_score >= 70 ORDER BY posted_at DESC
        Index("ix_posts_importance_posted", "importance_score", "posted_at"),
        # alert pipeline: WHERE alerts_processed_at IS NULL AND importance_score IS NOT NULL
        Index("ix_posts_alertqueue", "alerts_processed_at", "importance_score"),
    )
