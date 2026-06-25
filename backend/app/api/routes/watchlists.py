from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.watchlist_service import (
    add_watchlist_keyword,
    remove_watchlist_keyword,
    get_watchlist_news,
    analyze_watchlist_company,
    generate_watchlist_brief,
    calculate_market_health_cached,
    get_upcoming_events_cached,
    get_opportunities_risks_cached,
    get_sectors_intelligence_cached,
    search_global_smart
)
from app.services.financial_data import COMPANIES_MAP
from datetime import datetime
import uuid

router = APIRouter(tags=["Market Intelligence & Watchlists"])


@router.get("/watchlist")
@router.get("/api/watchlist")
@router.get("/api/watchlists")
@router.get("/watchlists")
def get_watchlists(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    
    # Sort: Attention Score descending, then Priority ascending (1 to 5), then Favorite first (favorite=True -> 0, favorite=False -> 1)
    def get_sort_key(item):
        score_val = 0
        if item.analysis_cache and isinstance(item.analysis_cache, dict):
            score_val = item.analysis_cache.get("attention_score", 0)
        inv_score_val = -score_val
        
        priority_val = item.priority if item.priority is not None else 3
        fav_val = 0 if item.favorite else 1
        
        return (inv_score_val, priority_val, fav_val)
        
    sorted_watchlists = sorted(watchlists, key=get_sort_key)
    
    return [
        {
            "id": str(w.id),
            "keyword": w.keyword,
            "company_name": w.company_name,
            "exchange": w.exchange,
            "sector": w.sector,
            "industry": w.industry,
            "notes": w.notes,
            "favorite": w.favorite,
            "priority": w.priority,
            "added_at": w.added_at.isoformat() if w.added_at else (w.created_at.isoformat() if w.created_at else None),
            "last_analyzed_at": w.last_analyzed_at.isoformat() if w.last_analyzed_at else None,
            "analysis_cache": w.analysis_cache
        }
        for w in sorted_watchlists
    ]


@router.post("/watchlist")
@router.post("/api/watchlist")
@router.post("/watchlists")
@router.post("/api/watchlist/add")
def add_watchlist(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    kw = data.get("keyword") or data.get("company_name")
    if not kw:
        raise HTTPException(status_code=400, detail="Keyword or company name is required")
        
    company_name = data.get("company_name", kw)
    exchange = data.get("exchange", "NSE")
    sector = data.get("sector")
    industry = data.get("industry")
    notes = data.get("notes")
    favorite = data.get("favorite", False)
    priority = data.get("priority", 3)
    
    w = add_watchlist_keyword(
        db, 
        keyword=kw, 
        user_id=current_user.id,
        company_name=company_name,
        exchange=exchange,
        notes=notes,
        favorite=favorite,
        priority=priority,
        sector=sector,
        industry=industry
    )
    
    try:
        analyze_watchlist_company(db, w.id, current_user.id, force=True)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Initial analysis failed on watchlist addition for {company_name}: {e}")

    return {
        "message": "Watchlist added successfully",
        "id": str(w.id),
        "keyword": w.keyword,
        "company_name": w.company_name,
        "exchange": w.exchange,
        "sector": w.sector,
        "industry": w.industry,
        "notes": w.notes,
        "favorite": w.favorite,
        "priority": w.priority,
        "added_at": w.added_at.isoformat() if w.added_at else None
    }


@router.delete("/watchlist/{watchlist_id}")
@router.delete("/api/watchlist/{watchlist_id}")
@router.delete("/watchlists/{watchlist_id}")
def delete_watchlist_endpoint(
    watchlist_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = remove_watchlist_keyword(db, watchlist_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
        
    return {
        "message": "Watchlist item removed successfully"
    }


@router.post("/watchlist/remove")
@router.post("/api/watchlist/remove")
def remove_watchlist_endpoint(
    data: dict, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    kw_or_id = data.get("keyword") or data.get("id") or data.get("company_name")
    if not kw_or_id:
        raise HTTPException(status_code=400, detail="Keyword, company name, or ID is required")
        
    success = remove_watchlist_keyword(db, kw_or_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
        
    return {
        "message": "Watchlist item removed successfully"
    }


@router.post("/watchlist/analyze")
@router.post("/api/watchlist/analyze")
def analyze_watchlist_endpoint(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    watchlist_id_str = data.get("watchlist_id") or data.get("id")
    if not watchlist_id_str:
        company_name = data.get("company_name")
        if not company_name:
            raise HTTPException(status_code=400, detail="watchlist_id or company_name is required")
        w = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id,
            Watchlist.company_name.ilike(company_name.strip())
        ).first()
        if not w:
            raise HTTPException(status_code=404, detail="Watchlist item not found for company")
        watchlist_id = w.id
    else:
        try:
            watchlist_id = uuid.UUID(watchlist_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid watchlist ID format")

    force = data.get("force", False)
    try:
        analysis = analyze_watchlist_company(db, watchlist_id, current_user.id, force=force)
        return analysis
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")


@router.post("/watchlist/brief")
@router.post("/api/watchlist/brief")
def brief_watchlist_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        brief = generate_watchlist_brief(db, current_user.id)
        return brief
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate watchlist brief: {str(e)}")


@router.get("/watchlist/search")
@router.get("/api/watchlist/search")
def search_companies_autocomplete(
    q: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q_clean = q.strip().lower()
    if not q_clean:
        return []
        
    matched = []
    seen = set()
    
    for val in COMPANIES_MAP.values():
        if q_clean in val.lower() and val not in seen:
            matched.append({"name": val, "exchange": "NSE" if val in ["TCS", "Infosys", "HDFC Bank", "Reliance Industries", "SBI", "Tata Motors"] else "NASDAQ"})
            seen.add(val)
            
    for key, val in COMPANIES_MAP.items():
        if q_clean in key and val not in seen:
            matched.append({"name": val, "exchange": "NSE" if val in ["TCS", "Infosys", "HDFC Bank", "Reliance Industries", "SBI", "Tata Motors"] else "NASDAQ"})
            seen.add(val)
            
    return matched[:10]


# ── Market Intelligence Engine REST APIs ──

@router.get("/api/market-intelligence/health")
def get_market_health(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return calculate_market_health_cached(db)


@router.get("/api/market-intelligence/events")
def get_upcoming_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_upcoming_events_cached(db)


@router.get("/api/market-intelligence/opportunities-risks")
def get_opportunities_risks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_opportunities_risks_cached(db)


@router.get("/api/market-intelligence/sectors")
def get_sectors_intelligence(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_sectors_intelligence_cached(db)


@router.get("/api/market-intelligence/search")
def get_global_smart_search(q: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return search_global_smart(db, q, current_user.id)