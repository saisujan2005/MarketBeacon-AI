from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.models.base import Base


class TweetNotification(Base):
    __tablename__ = "tweet_notifications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    handle = Column(String, nullable=False)
    label = Column(String, nullable=True)
    tweet_id = Column(String, unique=True, nullable=False)
    tweet_text = Column(String, nullable=False)
    tweet_url = Column(String, nullable=True)

    event_type = Column(String, nullable=True)
    importance_score = Column(Integer, nullable=True)

    # LLM-generated summary of why this tweet matters
    summary = Column(String, nullable=True)

    is_read = Column(Boolean, default=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )