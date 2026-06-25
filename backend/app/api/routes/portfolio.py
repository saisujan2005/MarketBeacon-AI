from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.holding import Holding
from app.services.portfolio_service import (
    calculate_portfolio_metrics,
    review_portfolio_ai,
    generate_portfolio_daily_brief,
    compile_holding_timeline,
    compare_holdings_metrics,
    clear_portfolio_cache
)
import uuid

router = APIRouter(tags=["Portfolio Intelligence & Risk Center"])


@router.get("/portfolio")
@router.get("/api/portfolio")
def get_portfolio(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        metrics = calculate_portfolio_metrics(db, current_user.id, force=force)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch portfolio metrics: {str(e)}"
        )


@router.post("/portfolio/holding")
@router.post("/api/portfolio/holding")
def add_holding(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_name = data.get("company_name")
    exchange = data.get("exchange", "NSE")
    quantity = data.get("quantity", 0.0)
    average_buy_price = data.get("average_buy_price", 0.0)
    notes = data.get("notes", "")
    tags = data.get("tags", [])

    if not company_name:
        raise HTTPException(status_code=400, detail="company_name is required.")
    
    try:
        quantity_f = float(quantity)
        buy_price_f = float(average_buy_price)
    except ValueError:
        raise HTTPException(status_code=400, detail="quantity and average_buy_price must be numerical.")

    inv_date = None
    if data.get("investment_date"):
        try:
            from datetime import datetime
            inv_date = datetime.strptime(data.get("investment_date"), "%Y-%m-%d")
        except ValueError:
            pass

    try:
        holding = Holding(
            user_id=current_user.id,
            company_name=company_name,
            exchange=exchange,
            quantity=quantity_f,
            average_buy_price=buy_price_f,
            notes=notes,
            tags=tags,
            investment_date=inv_date or datetime.utcnow()
        )
        db.add(holding)
        db.commit()
        db.refresh(holding)
        
        clear_portfolio_cache(current_user.id)
        return {"status": "success", "id": str(holding.id)}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create holding record: {str(e)}"
        )


@router.put("/portfolio/holding/{holding_id}")
@router.put("/api/portfolio/holding/{holding_id}")
def update_holding(
    holding_id: uuid.UUID,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found.")

    if "quantity" in data:
        try:
            holding.quantity = float(data["quantity"])
        except ValueError:
            raise HTTPException(status_code=400, detail="quantity must be numerical.")
            
    if "average_buy_price" in data:
        try:
            holding.average_buy_price = float(data["average_buy_price"])
        except ValueError:
            raise HTTPException(status_code=400, detail="average_buy_price must be numerical.")

    if "notes" in data:
        holding.notes = data["notes"]
    if "tags" in data:
        holding.tags = data["tags"]
    if "exchange" in data:
        holding.exchange = data["exchange"]

    try:
        db.commit()
        clear_portfolio_cache(current_user.id)
        return {"status": "success", "id": str(holding.id)}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update holding record: {str(e)}"
        )


@router.delete("/portfolio/holding/{holding_id}")
@router.delete("/api/portfolio/holding/{holding_id}")
def delete_holding(
    holding_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found.")

    try:
        db.delete(holding)
        db.commit()
        clear_portfolio_cache(current_user.id)
        return {"status": "success", "message": "Holding deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete holding record: {str(e)}"
        )


@router.get("/portfolio/review")
@router.get("/api/portfolio/review")
def get_portfolio_review(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        review = review_portfolio_ai(db, current_user.id, force=force)
        return review
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI Review execution failed: {str(e)}"
        )


@router.get("/portfolio/brief")
@router.get("/api/portfolio/brief")
def get_portfolio_daily_brief(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        brief = generate_portfolio_daily_brief(db, current_user.id, force=force)
        return brief
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate portfolio daily brief: {str(e)}"
        )


@router.get("/portfolio/timeline")
@router.get("/api/portfolio/timeline")
def get_holding_timeline_endpoint(
    company_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name parameter is required.")
    try:
        timeline = compile_holding_timeline(db, current_user.id, company_name)
        return timeline
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compile holding timeline: {str(e)}"
        )


@router.get("/portfolio/compare")
@router.get("/api/portfolio/compare")
def get_holding_comparison(
    co1: str,
    co2: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not co1 or not co2:
        raise HTTPException(status_code=400, detail="co1 and co2 parameters are required.")
    try:
        comparison = compare_holdings_metrics(db, current_user.id, co1, co2)
        return comparison
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


@router.get("/portfolio/risk")
@router.get("/api/portfolio/risk")
def get_portfolio_risk_center(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        metrics = calculate_portfolio_metrics(db, current_user.id)
        holdings = metrics["holdings"]
        
        # Sector concentration list
        sector_concentrations = sorted(
            metrics["sector_allocations"], 
            key=lambda x: x["percentage"], 
            reverse=True
        )
        
        # Single stock concentration
        stock_concentrations = sorted(
            [{"company_name": h["company_name"], "percentage": round(h["value"] / metrics["portfolio_value"] * 100.0, 2) if metrics["portfolio_value"] > 0 else 0.0} for h in holdings],
            key=lambda x: x["percentage"],
            reverse=True
        )
        
        # Research gaps (low confidence / missing reports)
        research_gaps = [h["company_name"] for h in holdings if not h["has_research"]]

        return {
            "health_score": metrics["health_score"],
            "health_status": metrics["health_status"],
            "sector_concentrations": sector_concentrations,
            "stock_concentrations": stock_concentrations,
            "research_gaps": research_gaps
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch portfolio risk details: {str(e)}"
        )
