import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ResearchDocument(Base):
    __tablename__ = "research_documents"

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

    title = Column(
        String(255),
        nullable=False
    )

    company_name = Column(
        String(255),
        nullable=True,
        index=True
    )

    document_type = Column(
        String(50),
        nullable=False,
        index=True
    )

    upload_date = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    file_path = Column(
        String(512),
        nullable=True
    )

    chunk_count = Column(
        Integer,
        default=0
    )

    embedding_model = Column(
        String(100),
        default="BAAI/bge-small-en-v1.5"
    )

    status = Column(
        String(20),
        default="Uploaded",
        index=True
    )

    user = relationship("User", back_populates="research_documents")
