from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceResponse

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("/", response_model=SourceResponse)
def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db)
):
    db_source = Source(
        platform=source.platform,
        handle=source.handle
    )

    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    return db_source


@router.get("/", response_model=list[SourceResponse])
def get_sources(
    db: Session = Depends(get_db)
):
    return db.query(Source).all()