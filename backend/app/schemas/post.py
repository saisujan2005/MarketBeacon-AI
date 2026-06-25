from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class PostResponse(BaseModel):
    id: UUID
    source_id: str | None
    title: str | None
    content: str | None
    post_url: str | None
    posted_at: datetime | None
    fetched_at: datetime

    model_config = ConfigDict(from_attributes=True)