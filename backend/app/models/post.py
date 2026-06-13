from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.models.base import Base
from sqlalchemy import Integer


class Post(Base):
    __tablename__ = "posts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=False
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