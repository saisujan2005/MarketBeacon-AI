import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="user")
    
    profile_picture = Column(String(512), nullable=True)
    timezone = Column(String(100), default="UTC")
    preferred_market = Column(String(100), default="US")
    subscription_plan = Column(String(50), default="free")

    # Relationships
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    chat_sessions = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    research_documents = relationship(
        "ResearchDocument",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    watchlists = relationship(
        "Watchlist",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    research_metrics = relationship(
        "ResearchMetric",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    daily_briefings = relationship(
        "DailyBriefing",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    alerts = relationship(
        "Alert",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    theme = Column(String(50), default="dark")
    language = Column(String(50), default="en")
    default_ai_model = Column(String(100), default="llama-3.3-70b-versatile")
    market_region = Column(String(100), default="US")
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    dashboard_layout = Column(String(100), default="default")
    watchlist_default = Column(String(100), default="default")
    daily_brief_time = Column(String(50), default="08:00")
    
    # Expanded notification preferences
    push_notifications = Column(Boolean, default=True)
    morning_brief = Column(Boolean, default=True)
    evening_summary = Column(Boolean, default=True)
    smart_alerts = Column(Boolean, default=True)
    watchlist_alerts = Column(Boolean, default=True)
    portfolio_alerts = Column(Boolean, default=True)
    weekly_digest = Column(Boolean, default=True)
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(50), default="22:00")
    quiet_hours_end = Column(String(50), default="08:00")
    timezone = Column(String(100), default="UTC")

    user = relationship("User", back_populates="preferences")
