import logging
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.holding import Holding
from app.models.watchlist import Watchlist
from app.models.post import Post
from app.models.alert import Alert
from app.models.research_document import ResearchDocument
from app.rag.llm_service import ask_llm
from app.services.financial_data import normalize_company_name, get_financial_provider
from app.services.explain_service import fetch_related_entities

logger = logging.getLogger(__name__)

# Global 30-minute cache for portfolio calculations
_PORTFOLIO_CACHE = {}

def get_cached_portfolio(key: str) -> dict:
    if key in _PORTFOLIO_CACHE:
        val, expiry = _PORTFOLIO_CACHE[key]
        if time.time() < expiry:
            return val
    return None

def set_cached_portfolio(key: str, val: dict, ttl_seconds: int = 1800):
    _PORTFOLIO_CACHE[key] = (val, time.time() + ttl_seconds)

def clear_portfolio_cache(user_id=None):
    """Clears all caches or user-specific cache on portfolio edits or new data feeds."""
    global _PORTFOLIO_CACHE
    if user_id:
        keys_to_del = [k for k in _PORTFOLIO_CACHE.keys() if str(user_id) in k]
        for k in keys_to_del:
            _PORTFOLIO_CACHE.pop(k, None)
        logger.info(f"[Portfolio Cache] Cleared cache for user: {user_id}")
    else:
        _PORTFOLIO_CACHE.clear()
        logger.info("[Portfolio Cache] Cleared all caches globally")

# Mapped current prices and daily change percentage for key companies
MOCK_MARKET_PRICES = {
    "HDFC Bank": {"price": 1650.00, "change_percent": 2.45, "sector": "Banking", "industry": "Private Banking"},
    "TCS": {"price": 3850.00, "change_percent": 1.25, "sector": "Technology", "industry": "IT Services"},
    "Infosys": {"price": 1480.00, "change_percent": -0.85, "sector": "Technology", "industry": "IT Services"},
    "Reliance Industries": {"price": 2850.00, "change_percent": -1.15, "sector": "Energy", "industry": "Oil & Gas"},
    "Tesla": {"price": 185.00, "change_percent": 3.12, "sector": "Automobile", "industry": "Electric Vehicles"},
    "Nvidia": {"price": 125.00, "change_percent": 4.85, "sector": "Technology", "industry": "Semiconductors"},
    "Tata Motors": {"price": 940.00, "change_percent": 0.45, "sector": "Automobile", "industry": "Auto Manufacturers"},
    "SBI": {"price": 780.00, "change_percent": 1.85, "sector": "Banking", "industry": "Public Banking"},
    "ICICI Bank": {"price": 1150.00, "change_percent": 1.10, "sector": "Banking", "industry": "Private Banking"}
}

def get_holding_price_info(company_name: str) -> dict:
    normalized = normalize_company_name(company_name)
    if normalized in MOCK_MARKET_PRICES:
        return MOCK_MARKET_PRICES[normalized]
    # Default fallback for unrecognized listings
    return {"price": 120.00, "change_percent": 0.00, "sector": "Other", "industry": "Unassigned"}

def calculate_portfolio_metrics(db: Session, user_id, force=False) -> dict:
    """
    Computes portfolio holdings values, allocations, Health Score, Diversification Score,
    and returns a fully aggregated payload.
    """
    cache_key = f"metrics:{user_id}"
    if not force:
        cached = get_cached_portfolio(cache_key)
        if cached:
            return cached

    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    
    # Standardize cash and equity assets
    cash_holding = next((h for h in holdings if h.company_name.upper() == "CASH"), None)
    cash_value = cash_holding.quantity if cash_holding else 0.0
    
    equity_holdings = [h for h in holdings if h.company_name.upper() != "CASH"]
    
    total_equity_value = 0.0
    total_cost_value = 0.0
    holdings_list = []
    
    sector_values = {}
    if cash_value > 0:
        sector_values["Cash"] = cash_value

    for h in equity_holdings:
        info = get_holding_price_info(h.company_name)
        curr_price = h.current_price if h.current_price is not None else info["price"]
        
        cost_value = h.quantity * h.average_buy_price
        curr_value = h.quantity * curr_price
        
        total_equity_value += curr_value
        total_cost_value += cost_value
        
        gain_loss = curr_value - cost_value
        gain_loss_pct = (gain_loss / cost_value * 100.0) if cost_value > 0 else 0.0
        
        sector = info["sector"]
        sector_values[sector] = sector_values.get(sector, 0.0) + curr_value
        
        # Calculate holding specific metadata (alerts, research counts)
        # News count past 7 days
        co_normalized = normalize_company_name(h.company_name)
        news_count = db.query(Post).filter(
            Post.content.ilike(f"%{co_normalized}%") | Post.title.ilike(f"%{co_normalized}%"),
            Post.posted_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Critical alerts past 7 days
        alerts_count = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.title.ilike(f"%{co_normalized}%"),
            Alert.importance_score >= 80,
            Alert.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Check research documents presence
        has_research = db.query(ResearchDocument).filter(
            ResearchDocument.user_id == user_id,
            ResearchDocument.company_name.ilike(co_normalized)
        ).count() > 0
        
        # Basic attention score logic: base 30 + updates
        attention_score = 30 + min(news_count * 5, 25) + min(alerts_count * 15, 45)
        if has_research:
            attention_score += 10
        attention_score = min(attention_score, 100)

        holdings_list.append({
            "id": str(h.id),
            "company_name": co_normalized,
            "exchange": h.exchange,
            "quantity": h.quantity,
            "average_buy_price": h.average_buy_price,
            "current_price": curr_price,
            "value": curr_value,
            "cost": cost_value,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
            "daily_change_pct": info["change_percent"],
            "daily_change_val": curr_value * (info["change_percent"] / 100.0),
            "sector": sector,
            "industry": info["industry"],
            "tags": h.tags or [],
            "notes": h.notes or "",
            "attention_score": attention_score,
            "has_research": has_research,
            "critical_alerts": alerts_count,
            "news_count": news_count,
            "investment_date": h.investment_date.strftime("%Y-%m-%d") if h.investment_date else None,
            "risk_level": "High" if attention_score >= 75 else "Medium" if attention_score >= 50 else "Low"
        })

    total_portfolio_value = total_equity_value + cash_value
    
    # Calculate allocations
    allocation_list = []
    for sector, val in sector_values.items():
        pct = (val / total_portfolio_value * 100.0) if total_portfolio_value > 0 else 0.0
        allocation_list.append({"sector": sector, "value": val, "percentage": round(pct, 2)})
    allocation_list.sort(key=lambda x: x["percentage"], reverse=True)

    # Health & Diversification scores
    num_sectors = len([sec for sec in sector_values.keys() if sec != "Cash"])
    diversification_score = 95 if num_sectors >= 4 else 80 if num_sectors == 3 else 50 if num_sectors == 2 else 20
    
    # Penalities: Concentration risk (max penalty 30 points)
    concentration_penalty = 0.0
    highest_stock_pct = 0.0
    largest_holding_name = "None"
    for item in holdings_list:
        stock_pct = (item["value"] / total_portfolio_value * 100.0) if total_portfolio_value > 0 else 0.0
        if stock_pct > highest_stock_pct:
            highest_stock_pct = stock_pct
            largest_holding_name = item["company_name"]
        if stock_pct > 30:
            concentration_penalty += (stock_pct - 30) * 0.5
            
    for item in allocation_list:
        if item["sector"] != "Cash" and item["percentage"] > 40:
            concentration_penalty += (item["percentage"] - 40) * 0.4
            
    concentration_penalty = min(concentration_penalty, 30.0)
    
    # Penalties: Alerts & news risks
    alert_penalty = sum([h["critical_alerts"] * 4 for h in holdings_list])
    risk_penalty = min(alert_penalty, 20.0)
    
    # Bonus: Research coverage
    research_covered = len([h for h in holdings_list if h["has_research"]])
    research_bonus = (research_covered / len(holdings_list) * 10.0) if holdings_list else 0.0
    
    health_score = round(60 + (diversification_score * 0.2) - concentration_penalty - risk_penalty + research_bonus)
    health_score = max(min(health_score, 100), 0)
    
    health_status = "Healthy" if health_score >= 80 else "Moderate Risk" if health_score >= 50 else "High Risk"

    # Daily changes
    today_equity_change_val = sum([h["daily_change_val"] for h in holdings_list])
    today_change_pct = (today_equity_change_val / total_portfolio_value * 100.0) if total_portfolio_value > 0 else 0.0

    # Top winners & losers
    sorted_by_change = sorted(holdings_list, key=lambda x: x["daily_change_pct"], reverse=True)
    top_winners = [s["company_name"] for s in sorted_by_change[:2] if s["daily_change_pct"] > 0]
    top_losers = [s["company_name"] for s in reversed(sorted_by_change) if s["daily_change_pct"] < 0][:2]

    # Mood classification
    mood = "Bullish" if today_change_pct > 0.5 else "Bearish" if today_change_pct < -0.5 else "Neutral"

    summary_payload = {
        "portfolio_value": round(total_portfolio_value, 2),
        "equity_value": round(total_equity_value, 2),
        "cash_value": round(cash_value, 2),
        "today_change_val": round(today_equity_change_val, 2),
        "today_change_pct": round(today_change_pct, 2),
        "health_score": health_score,
        "health_status": health_status,
        "diversification_score": diversification_score,
        "risk_level": "High" if health_score < 50 else "Medium" if health_score < 80 else "Low",
        "sector_allocations": allocation_list,
        "top_winners": top_winners,
        "top_losers": top_losers,
        "largest_holding": largest_holding_name,
        "mood": mood,
        "holdings": holdings_list
    }
    
    set_cached_portfolio(cache_key, summary_payload)
    return summary_payload


def review_portfolio_ai(db: Session, user_id, force=False) -> dict:
    """
    Feature 6: Generates a complete AI Portfolio review text based on current holdings.
    Contains research observation only, strictly avoiding buy/sell recommendations.
    """
    cache_key = f"review:{user_id}"
    if not force:
        cached = get_cached_portfolio(cache_key)
        if cached:
            return cached

    metrics = calculate_portfolio_metrics(db, user_id)
    holdings = metrics["holdings"]
    
    if not holdings:
        return {
            "summary": "Portfolio is currently empty. Add manual holdings to trigger AI review.",
            "strongest": [],
            "weakest": [],
            "risks": "No immediate risks detected.",
            "opportunities": "No immediate opportunities compiled.",
            "diversification_comments": "Empty portfolio lacks diversification.",
            "watchlist_priorities": []
        }

    holdings_str = "\n".join([
        f"- {h['company_name']}: Value: ₹{h['value']:.2f}, Allocation: {h['value']/metrics['portfolio_value']*100:.1f}%, Attention Score: {h['attention_score']}, News Count: {h['news_count']}, Critical Alerts: {h['critical_alerts']}, Risk Level: {h['risk_level']}"
        for h in holdings
    ])

    prompt = f"""You are a professional portfolio risk advisor at a top institutional bank.
Review the following manual investment holdings portfolio:

TOTAL PORTFOLIO VALUE: ₹{metrics['portfolio_value']:.2f}
CASH EXPOSURE: ₹{metrics['cash_value']:.2f}
HEALTH SCORE: {metrics['health_score']}/100 ({metrics['health_status']})
DIVERSIFICATION SCORE: {metrics['diversification_score']}/100

HOLDINGS DETAILS:
{holdings_str}

Analyze the concentration risk, recent alert frequencies, and macro alignment.
Do NOT give any buying, selling, or trading advice (e.g. do not say "sell HDFC Bank" or "buy TCS"). 
Instead, provide research observations, risk monitoring focus points, and historical context checkpoints.

Return a structured JSON review report.
Your response MUST be ONLY a valid JSON object in this exact schema (no markdown formatting, no surrounding wrappers):
{{
  "summary": "Cohesive overview paragraph regarding portfolio risk profile...",
  "strongest_holdings": ["TCS", "HDFC Bank"],
  "weakest_holdings": ["Reliance Industries"],
  "biggest_risks": "High concentration in Tech sector and alert alerts on HDFC Bank...",
  "biggest_opportunities": "IT valuations consolidation provides margin protection...",
  "diversification_comments": "Comments on allocation and cash reserves...",
  "suggested_priorities": [
    "Monitor RBI speech timelines for banking shifts",
    "Track energy commodity updates regarding reliance holdings"
  ]
}}
"""

    try:
        response = ask_llm(prompt, article_title="AI Portfolio Review Report")
        from app.services.explain_service import clean_json_output
        cleaned = clean_json_output(response)
        data = json.loads(cleaned)
        set_cached_portfolio(cache_key, data)
        return data
    except Exception as e:
        logger.error(f"Failed to compile AI Portfolio Review: {e}")
        fallback = {
            "summary": f"Your portfolio Health Score is {metrics['health_score']}. Volatility indicators reflect moderate exposure to sector alerts.",
            "strongest_holdings": [h["company_name"] for h in holdings[:2]],
            "weakest_holdings": [h["company_name"] for h in holdings[-1:]] if len(holdings) > 1 else [],
            "biggest_risks": "High alert volumes on major banking assets.",
            "biggest_opportunities": "Defensive margin rotation into Technology listings.",
            "diversification_comments": "Allocation reflects strong concentration in top 2 assets.",
            "suggested_priorities": ["Monitor recent news levels affecting top holdings."]
        }
        set_cached_portfolio(cache_key, fallback)
        return fallback


def generate_portfolio_daily_brief(db: Session, user_id, force=False) -> dict:
    """
    Feature 9: Generates the "Today's Portfolio Brief" narrative summary of changes,
    earnings updates, macro impacts, and attention areas.
    """
    cache_key = f"brief:{user_id}"
    if not force:
        cached = get_cached_portfolio(cache_key)
        if cached:
            return cached

    metrics = calculate_portfolio_metrics(db, user_id)
    holdings = metrics["holdings"]
    
    if not holdings:
        return {"brief": "Add holding assets to view personalized briefs."}

    companies_list = [h["company_name"] for h in holdings]
    
    # Grab recent alerts affecting portfolio
    recent_alerts = []
    for co in companies_list:
        alerts = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.title.ilike(f"%{co}%"),
            Alert.created_at >= datetime.utcnow() - timedelta(days=2)
        ).limit(2).all()
        for a in alerts:
            recent_alerts.append(f"{co}: {a.title}")

    prompt = f"""You are a Bloomberg-style morning portfolio strategist writing a personalized morning brief.
Analyze these holdings: {", ".join(companies_list)}.
Today's price movement: {metrics['today_change_pct']}% change.
Recent system alerts:
{chr(10).join(recent_alerts) if recent_alerts else "No immediate volatility alerts triggered."}

Write a short, professional briefing.
Return ONLY a valid JSON object in this exact schema (no markdown wrappers):
{{
  "title": "Today's Portfolio Brief Title...",
  "narrative": "Cohesive summary of how macro news and alerts affect holdings today...",
  "critical_changes": "Price fluctuations and volume developments across holdings...",
  "new_risks": "Negative catalysts identified in news/alerts...",
  "positive_developments": "Upgrades or positive margins...",
  "upcoming_events": [
    "RBI monetary speech tomorrow morning",
    "TCS Q1 earnings report scheduled Friday"
  ],
  "require_attention": ["HDFC Bank", "Reliance Industries"],
  "watch_tomorrow": ["TCS"]
}}
"""

    try:
        response = ask_llm(prompt, article_title="Portfolio Morning Brief")
        from app.services.explain_service import clean_json_output
        cleaned = clean_json_output(response)
        data = json.loads(cleaned)
        set_cached_portfolio(cache_key, data)
        return data
    except Exception as e:
        logger.error(f"Failed to generate Portfolio Morning Brief: {e}")
        fallback = {
            "title": "Portfolio Status: Stable Inflow Levels",
            "narrative": f"Holdings consolidated with a minor {metrics['today_change_pct']}% move. Watchlist indicators show low systemic volatility.",
            "critical_changes": "Assets trading in consolidative ranges.",
            "new_risks": "Energy sector pricing consolidation.",
            "positive_developments": "Steady private lender valuations.",
            "upcoming_events": ["Watch list earnings checkpoints coming up."],
            "require_attention": [h["company_name"] for h in holdings[:1]],
            "watch_tomorrow": [h["company_name"] for h in holdings[-1:]]
        }
        set_cached_portfolio(cache_key, fallback)
        return fallback


def compile_holding_timeline(db: Session, user_id, company_name: str) -> list:
    """
    Feature 7: Compiles a chronological timeline of news, alerts, research reports,
    and event catalysts related to a specific holding.
    """
    timeline = []
    co_normalized = normalize_company_name(company_name)

    # 1. Fetch News
    posts = db.query(Post).filter(
        Post.content.ilike(f"%{co_normalized}%") | Post.title.ilike(f"%{co_normalized}%")
    ).order_by(Post.posted_at.desc()).limit(5).all()
    for p in posts:
        timeline.append({
            "date": p.posted_at.strftime("%Y-%m-%d %H:%M") if p.posted_at else "Unknown",
            "timestamp": p.posted_at,
            "type": "News",
            "title": p.title,
            "badge": p.sentiment.upper() if p.sentiment else "NEUTRAL",
            "color": "#10b981" if p.sentiment == "Bullish" else "#ef4444" if p.sentiment == "Bearish" else "#64748b"
        })

    # 2. Fetch Alerts
    alerts = db.query(Alert).filter(
        Alert.user_id == user_id,
        Alert.title.ilike(f"%{co_normalized}%")
    ).order_by(Alert.created_at.desc()).limit(5).all()
    for a in alerts:
        timeline.append({
            "date": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "Unknown",
            "timestamp": a.created_at,
            "type": "Alert",
            "title": a.title,
            "badge": f"IMPORTANCE: {a.importance_score}",
            "color": "#06b6d4"
        })

    # 3. Fetch Research Documents
    reports = db.query(ResearchDocument).filter(
        ResearchDocument.user_id == user_id,
        ResearchDocument.company_name.ilike(co_normalized)
    ).order_by(ResearchDocument.upload_date.desc()).limit(5).all()
    for r in reports:
        timeline.append({
            "date": r.upload_date.strftime("%Y-%m-%d %H:%M") if r.upload_date else "Unknown",
            "timestamp": r.upload_date,
            "type": "Research",
            "title": f"Report Indexed: {r.title}",
            "badge": "DOC INDEXED",
            "color": "#a855f7"
        })

    # Sort chronological descending
    timeline.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Strip datetimes objects to serializable formats
    for t in timeline:
        t.pop("timestamp", None)
        
    return timeline


def compare_holdings_metrics(db: Session, user_id, co1: str, co2: str) -> dict:
    """
    Feature 11: Compiles dynamic comparison cards for two company assets.
    """
    provider = get_financial_provider()
    fund1 = provider.get_company_fundamentals(co1)
    fund2 = provider.get_company_fundamentals(co2)
    
    # Fetch alerts & news stats
    def get_stats(co):
        co_norm = normalize_company_name(co)
        news = db.query(Post).filter(
            Post.title.ilike(f"%{co_norm}%") | Post.content.ilike(f"%{co_norm}%"),
            Post.posted_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        alerts = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.title.ilike(f"%{co_norm}%"),
            Alert.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        return {"news_7d": news, "alerts_7d": alerts}
        
    s1 = get_stats(co1)
    s2 = get_stats(co2)
    
    return {
        "company1": {
            "name": normalize_company_name(co1),
            "fundamentals": fund1,
            "stats": s1,
            "timeline": compile_holding_timeline(db, user_id, co1)[:3]
        },
        "company2": {
            "name": normalize_company_name(co2),
            "fundamentals": fund2,
            "stats": s2,
            "timeline": compile_holding_timeline(db, user_id, co2)[:3]
        }
    }
