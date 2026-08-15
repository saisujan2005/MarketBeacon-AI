from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.dependencies import get_current_user
from app.models.user import User
from app.services.sector_intelligence import get_sector_intelligence

router = APIRouter()


@router.get("/sectors/heatmap")
def get_heatmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the aggregated sector intelligence for FMCG, Banking, IT, Auto, Pharma, Energy.
    """
    return get_sector_intelligence(db)
