from sqlalchemy import Column, String, Text, DateTime, Integer
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