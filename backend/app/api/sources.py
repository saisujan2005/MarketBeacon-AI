from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db, get_current_user, require_admin
from app.models.source import Source
from app.models.user import User
from app.schemas.source import SourceCreate, SourceResponse

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("/", response_model=SourceResponse)
def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Registers a new ingestion source.

    Sources are global platform configuration, so creation is restricted to
    administrators rather than any authenticated user.
    """
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Source).all()
