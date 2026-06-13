from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class PostResponse(BaseModel):
    id: UUID
    source_id: UUID
    title: str | None
    content: str | None
    post_url: str | None
    posted_at: datetime | None
    fetched_at: datetime

    class Config:
        from_attributes = True