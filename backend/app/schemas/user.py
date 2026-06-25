from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserPreferencesBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    theme: Optional[str] = "dark"
    language: Optional[str] = "en"
    default_ai_model: Optional[str] = "llama-3.3-70b-versatile"
    market_region: Optional[str] = "US"
    notifications_enabled: Optional[bool] = True
    email_notifications: Optional[bool] = True
    dashboard_layout: Optional[str] = "default"
    watchlist_default: Optional[str] = "default"
    daily_brief_time: Optional[str] = "08:00"


class UserPreferencesResponse(UserPreferencesBase):
    id: UUID
    user_id: UUID


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    email: EmailStr


class UserRegister(UserBase):
    password: str = Field(..., min_length=8)
    confirm_password: str

    model_config = ConfigDict(extra="forbid")


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False


class UserResponse(UserBase):
    id: UUID
    role: str
    is_active: bool
    is_verified: bool
    timezone: str
    preferred_market: str
    subscription_plan: str
    profile_picture: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    preferences: UserPreferencesBase | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    preferred_market: Optional[str] = None
    profile_picture: Optional[str] = None


class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    default_ai_model: Optional[str] = None
    market_region: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    dashboard_layout: Optional[str] = None
    watchlist_default: Optional[str] = None
    daily_brief_time: Optional[str] = None


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefresh(BaseModel):
    refresh_token: str
