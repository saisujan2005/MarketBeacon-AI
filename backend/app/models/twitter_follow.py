from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.models.base import Base


class TwitterFollow(Base):
    __tablename__ = "twitter_follows"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Twitter handle without @ e.g. "elonmusk"
    handle = Column(
        String,
        unique=True,
        nullable=False
    )

    # Display label e.g. "Elon Musk"
    label = Column(
        String,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    # Store the tweet_id of the last tweet we processed
    # so we don't reprocess old tweets on every poll
    last_tweet_id = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )