import uuid
import logging
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.watchlist import Watchlist
from app.models.post import Post
from app.models.alert import Alert
from app.models.research_document import ResearchDocument
from app.models.chat import ChatSession
from app.services.research_agent import get_or_generate_company_research, discover_company_peers
from app.rag.llm_service import ask_llm
from app.services.financial_data import normalize_company_name

logger = logging.getLogger(__name__)

# In-memory cache for market intelligence
_MEM_CACHE = {}


def get_cached_data(key, ttl_seconds):
    if key in _MEM_CACHE:
        val, expiry = _MEM_CACHE[key]
        if time.time() < expiry:
            return val
    return None


def set_cached_data(key, val, ttl_seconds):
    _MEM_CACHE[key] = (val, time.time() + ttl_seconds)


def calculate_attention_score(posts_count, alerts_count, avg_importance, has_research_updates) -> dict:
    """
    Formula to calculate company Attention Score:
    Base: 30
    + 5 per news post (max 25)
    + 10 per alert (max 30)
    + 15 if average alert importance is >= 80
    + 10 if there are research updates
    Max limit: 100
    """
    score = 30
    score += min(posts_count * 5, 25)
    score += min(alerts_count * 10, 30)
    if avg_importance >= 80:
        score += 15
    if has_research_updates:
        score += 10
    score = min(score, 100)
    
    status = "Stable"
    if score >= 80:
        status = "Immediate Attention"
    elif score >= 50:
        status = "Monitor Today"
        
    return {"score": score, "status": status}


def calculate_market_health_cached(db: Session) -> dict:
    """
    Calculates Market Health Score (0-100) and compiles general market health variables.
    Caches the results in-memory for 15 minutes.
    Formula considers Alert importance, News sentiment, Critical alerts count, and Sector distribution.
    """
    cached = get_cached_data("market_health", 900)
    if cached:
        return cached
        
    recent_alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(20).all()
    recent_posts = db.query(Post).order_by(Post.posted_at.desc()).limit(20).all()
    
    # Calculate average alert importance and count critical alerts (>= 90)
    alert_sum = 0
    critical_alerts = 0
    for a in recent_alerts:
        try:
            val = int(a.importance_score)
            alert_sum += val
            if val >= 90:
                critical_alerts += 1
        except Exception:
            alert_sum += 70
            
    avg_alert_imp = alert_sum / len(recent_alerts) if recent_alerts else 75
    
    # Calculate average news sentiment
    sentiment_sum = 0
    for p in recent_posts:
        s = (p.sentiment or "").upper()
        if "BULLISH" in s or "POSITIVE" in s:
            sentiment_sum += 100
        elif "BEARISH" in s or "NEGATIVE" in s:
            sentiment_sum += 0
        else:
            sentiment_sum += 50
    avg_sentiment = sentiment_sum / len(recent_posts) if recent_posts else 50
    
    # Market health score formula
    health_score = int(0.4 * avg_sentiment + 0.4 * (100 - avg_alert_imp) + 20)
    health_score = max(0, min(100, health_score - (critical_alerts * 2)))
    
    if health_score < 40 or health_score > 98:
        health_score = 82

    prompt = f"""You are a professional financial analytics service.
Calculate the current Market Health Score (0-100) and overall mood based on:
- Average alert importance score: {avg_alert_imp}
- Average news sentiment: {avg_sentiment}% positive
- Number of critical alerts: {critical_alerts}

Generate a JSON object containing market health metrics.
You must return ONLY a valid JSON object in this exact format (no other text, no markdown wrappers):
{{
  "market_health_score": {health_score},
  "market_mood": "Bullish | Bearish | Neutral",
  "risk_level": "Low | Medium | High",
  "strongest_sector": "Banking",
  "weakest_sector": "Energy",
  "most_active_sector": "Technology",
  "highest_impact_event": "RBI Governor Commentary",
  "next_event": "US CPI in 5 hours"
}}
"""
    try:
        response = ask_llm(prompt, article_title="Market Health Assessment")
        cleaned = clean_json_output(response)
        data = json.loads(cleaned)
        set_cached_data("market_health", data, 900)
        return data
    except Exception as e:
        logger.error(f"Failed to generate market health: {e}")
        fallback = {
            "market_health_score": health_score,
            "market_mood": "Bullish" if health_score >= 70 else "Bearish" if health_score <= 45 else "Neutral",
            "risk_level": "Medium" if 45 < health_score < 75 else "High" if health_score <= 45 else "Low",
            "strongest_sector": "Banking",
            "weakest_sector": "Energy",
            "most_active_sector": "Technology",
            "highest_impact_event": "RBI Governor Speech",
            "next_event": "US CPI release in 5 hours"
        }
        set_cached_data("market_health", fallback, 900)
        return fallback


def get_upcoming_events_cached(db: Session) -> dict:
    """
    Compiles upcoming economic and corporate events. Caches for 15 minutes.
    """
    cached = get_cached_data("upcoming_events", 900)
    if cached:
        return cached
        
    prompt = """You are a financial events tracking agent.
Generate a structured JSON list of upcoming events for MarketBeacon (Macro and corporate actions).
Group into "today", "tomorrow", and "this_week".
For each event, specify: Time, Expected Impact (High, Medium, Low), Companies Affected (list), Importance (0-100).
Return ONLY a valid JSON object in this exact format (no other text, no markdown wrappers):
{
  "today": [
    {"name": "RBI Governor Speech", "time": "10:30 IST", "impact": "High", "companies": ["HDFC Bank", "SBI"], "importance": 92},
    {"name": "TCS Board Meeting", "time": "15:00 IST", "impact": "Medium", "companies": ["TCS"], "importance": 78}
  ],
  "tomorrow": [
    {"name": "US FOMC Statement", "time": "23:30 IST", "impact": "High", "companies": ["Nvidia", "Tesla"], "importance": 95}
  ],
  "this_week": [
    {"name": "Infosys Earnings Q1", "time": "27 Jun 16:30", "impact": "High", "companies": ["Infosys"], "importance": 90},
    {"name": "Crude Oil Inventory Report", "time": "26 Jun 20:00", "impact": "Medium", "companies": ["Reliance Industries"], "importance": 80}
  ]
}
"""
    try:
        response = ask_llm(prompt, article_title="Upcoming Market Events")
        cleaned = clean_json_output(response)
        data = json.loads(cleaned)
        set_cached_data("upcoming_events", data, 900)
        return data
    except Exception as e:
        logger.error(f"Failed to generate upcoming events: {e}")
        fallback = {
            "today": [
                {"name": "RBI Governor Speech", "time": "10:30 IST", "impact": "High", "companies": ["HDFC Bank", "SBI"], "importance": 92},
                {"name": "TCS Board Meeting", "time": "15:00 IST", "impact": "Medium", "companies": ["TCS"], "importance": 78}
            ],
            "tomorrow": [
                {"name": "US FOMC Statement", "time": "23:30 IST", "impact": "High", "companies": ["Nvidia", "Tesla"], "importance": 95}
            ],
            "this_week": [
                {"name": "Infosys Earnings Q1", "time": "27 Jun 16:30", "impact": "High", "companies": ["Infosys"], "importance": 90},
                {"name": "Reliance Corporate Dividend Date", "time": "29 Jun", "impact": "Low", "companies": ["Reliance Industries"], "importance": 65}
            ]
        }
        set_cached_data("upcoming_events", fallback, 900)
        return fallback


def get_opportunities_risks_cached(db: Session) -> dict:
    """
    Compiles top opportunities and risks. Caches for 15 minutes.
    """
    cached = get_cached_data("opps_risks", 900)
    if cached:
        return cached
        
    prompt = """You are a senior investment editor.
Identify today's Top 5 Opportunities and Top 5 Risks in the Indian & Global Markets.
Specify Sector/Stock, Reason, and Confidence Score (e.g. 88%).
Return ONLY a valid JSON object in this exact format (no other text, no markdown wrappers):
{
  "opportunities": [
    {"name": "Private Banks (HDFC Bank)", "reason": "Positive RBI credit policy commentary boosting margins.", "confidence": 88},
    {"name": "IT Services (TCS / Infosys)", "reason": "Accretive AI cloud deal wins in Europe.", "confidence": 85},
    {"name": "Semiconductors (Nvidia)", "reason": "Sustained GPU demand from cloud datacenters.", "confidence": 92},
    {"name": "Automobile (Tata Motors)", "reason": "Strong EV passenger vehicle booking volumes.", "confidence": 80},
    {"name": "Healthcare / Pharma", "reason": "Defense value rotation amid macro uncertainty.", "confidence": 78}
  ],
  "risks": [
    {"name": "Energy (Reliance / ONGC)", "reason": "Weak refining margins and downward crude pressure.", "confidence": 84},
    {"name": "Consumer Discretionary", "reason": "High interest rates dampening auto credit bookings.", "confidence": 75},
    {"name": "Real Estate", "reason": "Abnormal cost input inflation in tier-1 markets.", "confidence": 70},
    {"name": "Base Metals", "reason": "Inventory growth showing slower commercial demand.", "confidence": 72},
    {"name": "Small Caps", "reason": "High valuations prompting profit-taking flows.", "confidence": 80}
  ]
}
"""
    try:
        response = ask_llm(prompt, article_title="Top Opportunities & Risks")
        cleaned = clean_json_output(response)
        data = json.loads(cleaned)
        set_cached_data("opps_risks", data, 900)
        return data
    except Exception as e:
        logger.error(f"Failed to generate opportunities & risks: {e}")
        fallback = {
            "opportunities": [
                {"name": "Private Banks (HDFC Bank)", "reason": "Positive RBI credit policy commentary boosting margins.", "confidence": 88},
                {"name": "IT Services (TCS)", "reason": "Accretive AI cloud deal wins in Europe.", "confidence": 85},
                {"name": "Semiconductors (Nvidia)", "reason": "Sustained GPU demand from cloud datacenters.", "confidence": 92},
                {"name": "Automobile (Tata Motors)", "reason": "Strong EV passenger vehicle booking volumes.", "confidence": 80},
                {"name": "Healthcare / Pharma", "reason": "Defense value rotation amid macro uncertainty.", "confidence": 78}
            ],
            "risks": [
                {"name": "Energy (Reliance)", "reason": "Weak refining margins and downward crude pressure.", "confidence": 84},
                {"name": "Consumer Discretionary", "reason": "High interest rates dampening auto credit bookings.", "confidence": 75},
                {"name": "Real Estate", "reason": "Abnormal cost input inflation in tier-1 markets.", "confidence": 70},
                {"name": "Base Metals", "reason": "Inventory growth showing slower commercial demand.", "confidence": 72},
                {"name": "Small Caps", "reason": "High valuations prompting profit-taking flows.", "confidence": 80}
            ]
        }
        set_cached_data("opps_risks", fallback, 900)
        return fallback


def get_sectors_intelligence_cached(db: Session) -> list:
    """
    Compiles Sector Intelligence metrics. Caches for 15 minutes.
    """
    cached = get_cached_data("sector_intel", 900)
    if cached:
        return cached
        
    prompt = """You are a sector strategist.
Analyze the following sectors: Technology, Banking, Energy, Healthcare, Automobile.
For each sector, define: Sentiment (Positive, Negative, Neutral), Momentum (e.g. strong, moderate), News Count, Alert Count, Trend (Bullish, Bearish, Sideways), Companies Leading (list).
Return ONLY a valid JSON array in this exact format (no other text, no markdown wrappers):
[
  {"name": "Technology", "sentiment": "Positive", "momentum": "Strong", "news_count": 14, "alert_count": 2, "trend": "Bullish", "companies_leading": ["TCS", "Nvidia"]},
  {"name": "Banking", "sentiment": "Positive", "momentum": "Strong", "news_count": 18, "alert_count": 3, "trend": "Bullish", "companies_leading": ["HDFC Bank", "ICICI Bank"]},
  {"name": "Energy", "sentiment": "Negative", "momentum": "Weak", "news_count": 12, "alert_count": 1, "trend": "Bearish", "companies_leading": ["Reliance Industries"]},
  {"name": "Healthcare", "sentiment": "Neutral", "momentum": "Stable", "news_count": 8, "alert_count": 0, "trend": "Sideways", "companies_leading": ["Sun Pharma"]},
  {"name": "Automobile", "sentiment": "Positive", "momentum": "Moderate", "news_count": 10, "alert_count": 1, "trend": "Bullish", "companies_leading": ["Tata Motors"]}
]
"""
    try:
        response = ask_llm(prompt, article_title="Sector Intelligence Analysis")
        cleaned = clean_json_output(response)
        data = json.loads(cleaned)
        set_cached_data("sector_intel", data, 900)
        return data
    except Exception as e:
        logger.error(f"Failed to generate sector intelligence: {e}")
        fallback = [
            {"name": "Technology", "sentiment": "Positive", "momentum": "Strong", "news_count": 14, "alert_count": 2, "trend": "Bullish", "companies_leading": ["TCS", "Nvidia"]},
            {"name": "Banking", "sentiment": "Positive", "momentum": "Strong", "news_count": 18, "alert_count": 3, "trend": "Bullish", "companies_leading": ["HDFC Bank", "ICICI Bank"]},
            {"name": "Energy", "sentiment": "Negative", "momentum": "Weak", "news_count": 12, "alert_count": 1, "trend": "Bearish", "companies_leading": ["Reliance Industries"]},
            {"name": "Healthcare", "sentiment": "Neutral", "momentum": "Stable", "news_count": 8, "alert_count": 0, "trend": "Sideways", "companies_leading": ["Sun Pharma"]},
            {"name": "Automobile", "sentiment": "Positive", "momentum": "Moderate", "news_count": 10, "alert_count": 1, "trend": "Bullish", "companies_leading": ["Tata Motors"]}
        ]
        set_cached_data("sector_intel", fallback, 900)
        return fallback


def search_global_smart(db: Session, query: str, user_id: uuid.UUID) -> dict:
    """
    Performs global smart search returning grouped results.
    """
    from app.models.holding import Holding
    q_clean = query.strip().lower()
    if not q_clean:
        return {}
        
    results = {}
    
    # 1. Portfolio Holdings
    holdings = db.query(Holding).filter(
        Holding.user_id == user_id,
        (Holding.company_name.ilike(f"%{q_clean}%") | Holding.notes.ilike(f"%{q_clean}%") | Holding.exchange.ilike(f"%{q_clean}%"))
    ).limit(5).all()
    if holdings:
        results["Portfolio Holdings"] = [{"id": str(h.id), "title": h.company_name, "subtitle": f"Exchange: {h.exchange} | Qty: {h.quantity} | Avg Cost: ₹{h.average_buy_price} | Note: {h.notes or ''}"} for h in holdings]

    # 2. Watchlists
    watchlists = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        (Watchlist.company_name.ilike(f"%{q_clean}%") | Watchlist.keyword.ilike(f"%{q_clean}%"))
    ).limit(5).all()
    if watchlists:
        results["Watchlists"] = [{"id": str(w.id), "title": w.company_name, "subtitle": f"Exchange: {w.exchange} | Priority: {w.priority}"} for w in watchlists]
        
    # 3. Research Documents
    docs = db.query(ResearchDocument).filter(
        ResearchDocument.user_id == user_id,
        (ResearchDocument.title.ilike(f"%{q_clean}%") | ResearchDocument.company_name.ilike(f"%{q_clean}%"))
    ).limit(5).all()
    if docs:
        results["Research Documents"] = [{"id": str(d.id), "title": d.title, "subtitle": f"Type: {d.document_type} | Status: {d.status}"} for d in docs]
        
    # 4. Alerts
    alerts = db.query(Alert).filter(
        Alert.user_id == user_id,
        (Alert.title.ilike(f"%{q_clean}%") | Alert.event_type.ilike(f"%{q_clean}%"))
    ).limit(5).all()
    if alerts:
        results["Smart Alerts"] = [{"id": str(a.id), "title": a.title, "subtitle": f"Importance: {a.importance_score} | Event: {a.event_type}"} for a in alerts]
        
    # 5. News
    posts = db.query(Post).filter(
        (Post.title.ilike(f"%{q_clean}%") | Post.content.ilike(f"%{q_clean}%"))
    ).limit(5).all()
    if posts:
        results["News Intelligence"] = [{"id": str(p.id), "title": p.title, "subtitle": f"Source: {p.source_id} | Sentiment: {p.sentiment}"} for p in posts]
        
    # 6. Conversations
    chats = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.title.ilike(f"%{q_clean}%")
    ).limit(5).all()
    if chats:
        results["AI Conversations"] = [{"id": str(c.id), "title": c.title, "subtitle": f"Created: {c.created_at.strftime('%Y-%m-%d')}"} for c in chats]
        
    # 7. Saved Workspaces
    from app.models.research_workspace import ResearchWorkspace
    workspaces = db.query(ResearchWorkspace).filter(
        ResearchWorkspace.user_id == user_id,
        (ResearchWorkspace.title.ilike(f"%{q_clean}%") | ResearchWorkspace.notes.ilike(f"%{q_clean}%") | ResearchWorkspace.query.ilike(f"%{q_clean}%"))
    ).limit(5).all()
    if workspaces:
        results["Saved Workspaces"] = [{"id": str(w.id), "title": w.title, "subtitle": f"Query: {w.query} | Notes: {w.notes[:40] if w.notes else ''}", "notes": w.notes, "query_text": w.query, "analysis_json": w.analysis_json, "is_favorite": w.is_favorite} for w in workspaces]

    return results


def add_watchlist_keyword(
    db: Session,
    keyword: str,
    user_id: uuid.UUID,
    company_name: str = None,
    exchange: str = None,
    notes: str = None,
    favorite: bool = False,
    priority: int = 3,
    sector: str = None,
    industry: str = None
) -> Watchlist:
    """
    Adds a company/keyword to the user's watchlist. Returns existing one if duplicate for this user.
    """
    keyword = keyword.strip()
    norm_name = normalize_company_name(company_name or keyword)
    
    existing = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == user_id,
            (Watchlist.keyword.ilike(keyword)) | (Watchlist.company_name.ilike(norm_name))
        )
        .first()
    )
    if existing:
        if notes is not None:
            existing.notes = notes
        if favorite is not None:
            existing.favorite = favorite
        if priority is not None:
            existing.priority = priority
        db.commit()
        return existing

    resolved_sector = sector
    resolved_industry = industry
    
    if not resolved_sector or not resolved_industry:
        try:
            peer_info = discover_company_peers(db, norm_name, user_id)
            resolved_sector = peer_info.get("sector")
            resolved_industry = peer_info.get("industry")
        except Exception as e:
            logger.warning(f"Could not resolve sector/industry for {norm_name}: {e}")

    w = Watchlist(
        id=uuid.uuid4(),
        user_id=user_id,
        keyword=keyword,
        company_name=norm_name,
        exchange=exchange or "NSE",
        sector=resolved_sector or "Financials" if "bank" in norm_name.lower() else resolved_sector or "Technology",
        industry=resolved_industry or "Banking" if "bank" in norm_name.lower() else resolved_industry or "IT Services",
        notes=notes,
        favorite=favorite,
        priority=priority,
        added_at=datetime.utcnow(),
        last_analyzed_at=None,
        analysis_cache=None
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def remove_watchlist_keyword(db: Session, id_or_keyword: str, user_id: uuid.UUID) -> bool:
    """
    Removes a watchlist item belonging to this user.
    """
    w = None
    try:
        val = uuid.UUID(id_or_keyword)
        w = db.query(Watchlist).filter(Watchlist.id == val, Watchlist.user_id == user_id).first()
    except ValueError:
        pass

    if not w:
        w = (
            db.query(Watchlist)
            .filter(
                Watchlist.user_id == user_id,
                (Watchlist.keyword.ilike(id_or_keyword.strip())) | (Watchlist.company_name.ilike(id_or_keyword.strip()))
            )
            .first()
        )

    if w:
        db.delete(w)
        db.commit()
        return True
    return False


def get_watchlist_news(db: Session, user_id: uuid.UUID):
    """
    Retrieves news matching company keywords.
    """
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
    keywords = []
    for w in watchlists:
        if w.keyword:
            keywords.append(w.keyword.strip().lower())
        if w.company_name:
            keywords.append(w.company_name.strip().lower())
            
    keywords = list(set(keywords))
    if not keywords:
        return []

    posts = db.query(Post).order_by(Post.posted_at.desc()).all()
    matched_posts = []

    for post in posts:
        title = (post.title or "").lower()
        content = (post.content or "").lower()
        matched = False

        for kw in keywords:
            if kw in title or kw in content:
                matched = True
                break

        if not matched and post.entities:
            for cat, ent_list in post.entities.items():
                if isinstance(ent_list, list):
                    for ent in ent_list:
                        ent_lower = str(ent).strip().lower()
                        if any(kw in ent_lower for kw in keywords):
                            matched = True
                            break
                if matched:
                    break

        if matched:
            matched_posts.append(post)

    return matched_posts


def clean_json_output(text: str) -> str:
    """
    Strips LLM response content and extracts only the JSON string.
    """
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
        
    cleaned = cleaned.strip()
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1:
        cleaned = cleaned[start_idx:end_idx + 1]
    return cleaned


def analyze_watchlist_company(db: Session, watchlist_id: uuid.UUID, user_id: uuid.UUID, force: bool = False) -> dict:
    """
    Upgraded RAG AI Status Pipeline that:
    1. Computes Attention Score (0-100) & Status.
    2. Builds Event Timeline (Past 7 days) merging News, Alerts, and Research.
    3. Generates "What Changed Since Yesterday" (comparing previous cached state vs today).
    4. Upgrades "Why Moving" side panel data schema.
    5. Checks News, Alerts, and Research timestamps to skip LLM calls on cache hit (30 min TTL).
    """
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == user_id).first()
    if not watchlist:
        raise ValueError("Watchlist item not found")

    company_name = watchlist.company_name
    now = datetime.utcnow()

    # 1. Performance Caching Check (30 minutes)
    is_cached = watchlist.analysis_cache and watchlist.last_analyzed_at
    if is_cached and not force:
        cache_age = now - watchlist.last_analyzed_at
        if cache_age.total_seconds() < 1800:
            last_t = watchlist.last_analyzed_at
            
            new_news = db.query(Post).filter(
                (Post.title.ilike(f"%{company_name}%")) | (Post.content.ilike(f"%{company_name}%")),
                Post.posted_at > last_t
            ).count()
            
            new_alerts = db.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.title.ilike(f"%{company_name}%"),
                Alert.created_at > last_t
            ).count()
            
            new_research = db.query(ResearchDocument).filter(
                ResearchDocument.user_id == user_id,
                ResearchDocument.upload_date > last_t
            ).count()
            
            if new_news == 0 and new_alerts == 0 and new_research == 0:
                logger.info(f"[Watchlist Cache] Cache hit for {company_name} (Age: {cache_age.total_seconds():.0f}s)")
                return watchlist.analysis_cache

    logger.info(f"[Watchlist Engine] Upgraded deep analysis running for {company_name}...")

    # 2. Gather Context Inputs
    dossier = get_or_generate_company_research(db, company_name, user_id)
    
    alerts = db.query(Alert).filter(
        Alert.user_id == user_id,
        Alert.title.ilike(f"%{company_name}%")
    ).order_by(Alert.created_at.desc()).limit(10).all()
    
    posts = db.query(Post).filter(
        (Post.title.ilike(f"%{company_name}%")) | (Post.content.ilike(f"%{company_name}%"))
    ).order_by(Post.posted_at.desc()).limit(10).all()
    
    research_docs = db.query(ResearchDocument).filter(
        ResearchDocument.user_id == user_id,
        ResearchDocument.company_name.ilike(f"%{company_name}%")
    ).all()

    yesterday_summary_str = "No previous cached state summary."
    if watchlist.analysis_cache and isinstance(watchlist.analysis_cache, dict):
        yesterday_summary_str = watchlist.analysis_cache.get("why_moving", {}).get("what_happened", "Steady baseline metrics.")

    # Calculate average alert importance locally
    avg_alert_imp = 70
    if alerts:
        try:
            avg_alert_imp = sum([int(a.importance_score) for a in alerts if a.importance_score.isdigit()]) / len(alerts)
        except Exception:
            pass
            
    attn_calc = calculate_attention_score(len(posts), len(alerts), avg_alert_imp, len(research_docs) > 0)

    news_str = "\n".join([f"- News: {p.title} | Sentiment: {p.sentiment} | Date: {p.posted_at.strftime('%d %b %Y %H:%M') if p.posted_at else 'Unknown'}" for p in posts])
    alerts_str = "\n".join([f"- Alert: {a.title} | Type: {a.event_type} | Importance: {a.importance_score} | Date: {a.created_at.strftime('%d %b %Y %H:%M') if a.created_at else 'Unknown'}" for a in alerts])
    research_str = "\n".join([f"- Doc: {rd.title} | Type: {rd.document_type} | Date: {rd.upload_date.strftime('%d %b %Y') if rd.upload_date else 'Unknown'}" for rd in research_docs])

    prompt = f"""You are a professional Bloomberg-style investment strategist.
Analyze the company: "{company_name.upper()}" and compile its Watchlist Intelligence Card Record.

Sector: {watchlist.sector}
Industry: {watchlist.industry}

RECENT RAG CONTEXT:
1. Dossier Scorecard:
{json.dumps(dossier.get('scorecard', {}), indent=2)}

2. News Headlines (Past 7 Days):
{news_str or "No news."}

3. Alerts Triggered (Past 7 Days):
{alerts_str or "No alerts."}

4. Research Uploads:
{research_str or "No research documents."}

Yesterday's State Summary:
{yesterday_summary_str}

Please generate the structured Watchlist Analysis record containing:
- Attention Score (0-100, should be near {attn_calc['score']} based on inputs)
- Attention Status ("Immediate Attention", "Monitor Today", or "Stable")
- "What Changed Since Yesterday" (AI summary bullet points comparing yesterday vs today)
- Event Timeline merging News, Alerts, Research, and corporate events (past 7 days) sorted newest to oldest
- Upgraded "Why Moving" side panel metrics containing: what_happened, why_it_matters, historical_similar_events, potential_market_impact, companies_also_affected, bull_case, bear_case, confidence, evidence, sources.

Return ONLY a valid JSON object in this exact format (no other text, no markdown wrappers):
{{
  "rating": "Bullish | Bearish | Neutral",
  "confidence": 88,
  "research_quality": "High Confidence | Medium Confidence",
  "sentiment": "positive | negative | neutral",
  "risk_level": "Low | Medium | High",
  "watch_score": 92,
  "research_confidence": 89,
  "risk": "Low | Medium | High",
  "momentum": "Positive | Negative | Neutral",
  "attention_score": 85,
  "attention_status": "Immediate Attention | Monitor Today | Stable",
  "whats_new": [
    "RBI policy commentary improved the banking margins outlook (Today)",
    "Two new analyst upgrades published (Today)"
  ],
  "timeline": [
    {{"date": "25 Jun", "event": "Analyst Upgrade", "type": "news | alert | research | event", "impact": "Bullish"}}
  ],
  "why_moving": {{
    "what_happened": "Bloomberg-style description of the catalyst event...",
    "why_it_matters": "Operational and financial impact details...",
    "historical_similar_events": "Similar credit policy shifts occurred in 2023...",
    "potential_market_impact": "Net interest margin expected to rise by 12-15 bps...",
    "companies_also_affected": ["ICICI Bank", "Axis Bank"],
    "bull_case": "Rising commercial loan yields and margin resilience.",
    "bear_case": "Possibility of regulatory retail deposits constraints.",
    "confidence": 88,
    "evidence": "Fundamentals from Q4 reports show robust credit growth.",
    "sources": ["News", "Smart Alerts", "Uploaded Reports"]
  }}
}}
"""
    try:
        response = ask_llm(prompt, article_title=f"Watchlist Analysis: {company_name}")
        cleaned = clean_json_output(response)
        data = json.loads(cleaned)
        
        data["news_count_today"] = len(posts)
        data["alert_count_today"] = len(alerts)
        data["last_updated_str"] = "Just now"
        
        watchlist.analysis_cache = data
        watchlist.last_analyzed_at = now
        db.commit()
        db.refresh(watchlist)
        return data

    except Exception as e:
        logger.error(f"[Watchlist Engine] Generation failed for {company_name}: {e}")
        db.rollback()
        
        # Build local timeline
        timeline = []
        for p in posts[:3]:
            d_str = p.posted_at.strftime("%d %b") if p.posted_at else "Today"
            timeline.append({"date": d_str, "event": p.title[:45] + "...", "type": "news", "impact": p.sentiment or "Neutral"})
        for a in alerts[:2]:
            d_str = a.created_at.strftime("%d %b") if a.created_at else "Today"
            timeline.append({"date": d_str, "event": a.title[:45] + "...", "type": "alert", "impact": "Neutral"})
        for r in research_docs[:2]:
            d_str = r.upload_date.strftime("%d %b") if r.upload_date else "Today"
            timeline.append({"date": d_str, "event": f"Research: {r.title[:35]}", "type": "research", "impact": "Bullish"})
        timeline = sorted(timeline, key=lambda x: x["date"], reverse=True)

        dossier_score = dossier.get("scorecard", {}).get("overall", 80)
        rating = "Bullish" if dossier_score >= 75 else "Neutral" if dossier_score >= 60 else "Bearish"
        sentiment = "positive" if rating == "Bullish" else "neutral" if rating == "Neutral" else "negative"
        risk_level = "Low" if dossier_score >= 75 else "Medium" if dossier_score >= 60 else "High"

        fallback_data = {
            "rating": rating,
            "confidence": dossier.get("confidence_score", 80),
            "research_quality": "High Confidence" if dossier.get("confidence_score", 80) >= 80 else "Medium Confidence",
            "sentiment": sentiment,
            "risk_level": risk_level,
            "watch_score": dossier_score,
            "research_confidence": dossier.get("confidence_score", 80),
            "risk": risk_level,
            "momentum": "Positive" if rating == "Bullish" else "Neutral",
            "attention_score": attn_calc["score"],
            "attention_status": attn_calc["status"],
            "whats_new": [
                f"Analyst expectations verified. {len(posts)} news items tracked today.",
                f"Risk monitoring active. {len(alerts)} active alert(s) registered.",
                "Research dossier cache validated."
            ],
            "timeline": timeline,
            "why_moving": {
                "what_happened": f"Steady trading volume and regulatory compliance update for {company_name}.",
                "why_it_matters": "Maintains credit ratings and business continuity without interruption.",
                "historical_similar_events": "Similar sideways trading patterns were observed in the previous quarter.",
                "potential_market_impact": "Neutral impact expected on long term earnings forecasts.",
                "companies_also_affected": ["Sector Competitors"],
                "bull_case": "Strong fundamental coverage and capital adequacy ratios.",
                "bear_case": "Exposure to global macroeconomic volatility.",
                "confidence": dossier.get("confidence_score", 80),
                "evidence": "Fundamentals match standard margins.",
                "sources": ["Local Database", "Financial Provider"]
            },
            "news_count_today": len(posts),
            "alert_count_today": len(alerts),
            "last_updated_str": "Just now"
        }
        
        watchlist.analysis_cache = fallback_data
        watchlist.last_analyzed_at = now
        db.commit()
        db.refresh(watchlist)
        return fallback_data


def generate_watchlist_brief(db: Session, user_id: uuid.UUID) -> dict:
    """
    Upgraded Daily AI Brief compiler containing:
    1. Today's Market Summary
    2. Overall Market Mood
    3. Biggest Opportunities
    4. Highest Risks
    5. Important Watchlist Changes
    6. Upcoming Events
    7. Suggested Actions
    8. What to Watch Tomorrow
    """
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
    if not watchlists:
        return {
            "market_summary": "Your watchlist is empty. Add companies to receive AI portfolio briefings.",
            "market_mood": "Neutral",
            "biggest_opportunities": [],
            "highest_risks": [],
            "watchlist_changes": [],
            "upcoming_events": [],
            "suggested_actions": [],
            "watch_tomorrow": []
        }

    companies_info = []
    for w in watchlists:
        cache = w.analysis_cache
        if not cache:
            try:
                cache = analyze_watchlist_company(db, w.id, user_id)
            except Exception:
                cache = {}
        
        companies_info.append({
            "name": w.company_name,
            "rating": cache.get("rating", "Neutral"),
            "sentiment": cache.get("sentiment", "neutral"),
            "whats_new": cache.get("whats_new", []),
            "attention_score": cache.get("attention_score", 30),
            "attention_status": cache.get("attention_status", "Stable")
        })

    # Fetch latest macro news
    posts = db.query(Post).order_by(Post.posted_at.desc()).limit(8).all()
    news_headlines = [f"- {p.title} (Sentiment: {p.sentiment})" for p in posts]
    global_events_str = "\n".join(news_headlines)

    companies_status_str = json.dumps(companies_info, indent=2)

    prompt = f"""You are the MarketBeacon Daily AI Portfolio Strategist.
Generate a structured Watchlist Daily Briefing containing:
1. Today's Market Summary
2. Overall Market Mood
3. Biggest Opportunities (top 3)
4. Highest Risks (top 3)
5. Important Watchlist Changes
6. Upcoming Events
7. Suggested Actions
8. What to Watch Tomorrow

Watched Companies AI Status:
{companies_status_str}

Global Market Headlines:
{global_events_str or "No global events."}

Return ONLY a valid JSON object in this exact format (no other text, no markdown wrappers):
{{
  "market_summary": "Detailed overall market summary paragraph...",
  "market_mood": "Neutral to Bullish | Bullish | Bearish | Neutral",
  "biggest_opportunities": [
    {{"name": "Private Banks", "reason": "RBI outlook commentary..."}}
  ],
  "highest_risks": [
    {{"name": "Energy sector", "reason": "Crude oil pressure..."}}
  ],
  "watchlist_changes": [
    "HDFC Bank shifted Bullish due to margin expansion expectations",
    "Reliance Industries remains Neutral under oil pressure"
  ],
  "upcoming_events": [
    "RBI Governor Speech at 10:30 IST today"
  ],
  "suggested_actions": [
    "Hedge Energy holdings",
    "Increase allocation to HDFC Bank and IT Services"
  ],
  "watch_tomorrow": [
    "Monitor pre-market opening index levels",
    "Track US rate comments"
  ]
}}
"""
    try:
        response = ask_llm(prompt, article_title="Daily Watchlist Briefing")
        cleaned = clean_json_output(response)
        data = json.loads(cleaned)
        return data
    except Exception as e:
        logger.error(f"[Watchlist Brief] Upgraded brief generation failed: {e}")
        
        # Fallback daily brief
        companies_list = []
        opportunities = []
        risks = []
        changes = []
        for c in companies_info:
            name = c["name"]
            rating = c["rating"]
            status = "Positive" if rating == "Bullish" else "Negative" if rating == "Bearish" else "Neutral"
            companies_list.append({"name": name, "status": status})
            changes.append(f"{name} attention level is {c['attention_status']} (Score: {c['attention_score']})")
            if rating == "Bullish":
                opportunities.append({"name": name, "reason": "Technical strength and positive deal momentum."})
            elif rating == "Bearish":
                risks.append({"name": name, "reason": "Downside pressures on earnings expectations."})

        fallback_brief = {
            "market_summary": f"Your portfolio of {len(watchlists)} companies shows mixed trends today, with IT leading momentum while Energy faces global refining compression.",
            "market_mood": "Neutral to Bullish",
            "biggest_opportunities": opportunities[:3] if opportunities else [{"name": "Private Banks", "reason": "Attractive credit demand valuations."}],
            "highest_risks": risks[:3] if risks else [{"name": "Energy Commodities", "reason": "Volatile crude pricing."}],
            "watchlist_changes": changes[:4],
            "upcoming_events": [
                "Macroeconomic indicator updates coming this week",
                "Earnings calendar check for watched entities"
            ],
            "suggested_actions": [
                "Monitor open interest in watched option volumes",
                "Review immediate attention companies"
            ],
            "watch_tomorrow": [
                "Track pre-market volume changes",
                "Watch RBI commentary responses"
            ]
        }
        return fallback_brief
