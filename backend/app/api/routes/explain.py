from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.explain_service import explain_item, generate_daily_market_story

router = APIRouter(tags=["AI Explain Engine & Market Stories"])


@router.post("/api/explain")
@router.post("/explain")
def post_explain_anything(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item_type = data.get("item_type")
    item_id = data.get("item_id")
    text = data.get("text")
    force = data.get("force", False)

    if not item_type or not (item_id or text):
        raise HTTPException(
            status_code=400,
            detail="item_type and either item_id or text are required."
        )

    valid_types = ["news", "alert", "company", "event", "text"]
    if item_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid item_type. Must be one of {valid_types}"
        )

    try:
        explanation = explain_item(
            db=db,
            item_type=item_type,
            item_id_or_name=item_id or "",
            highlighted_text=text,
            user_id=current_user.id,
            force=force
        )
        return explanation
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Explain Engine execution error: {str(e)}"
        )


@router.get("/api/market-intelligence/story")
@router.get("/market-intelligence/story")
def get_daily_market_story(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        story = generate_daily_market_story(db, user_id=current_user.id)
        return story
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Daily Market Story: {str(e)}"
        )
