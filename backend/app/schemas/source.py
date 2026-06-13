from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class SourceCreate(BaseModel):
    platform: str
    handle: str


class SourceResponse(BaseModel):
    id: UUID
    platform: str
    handle: str
    created_at: datetime

    class Config:
        from_attributes = True