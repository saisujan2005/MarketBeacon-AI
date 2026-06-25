import logging

logger = logging.getLogger(__name__)

# Reliability mapping definitions
SOURCE_TIER_MAPPING = {
    "annual report": {"tier": 1, "weight": 1.0, "label": "Tier 1: Annual Report", "description": "Verified Regulatory Annual Reports"},
    "regulatory filing": {"tier": 1, "weight": 1.0, "label": "Tier 1: Regulatory Filing", "description": "Official Exchange & Regulatory Filings"},
    "earnings call": {"tier": 1, "weight": 1.0, "label": "Tier 1: Earnings Call", "description": "Management Earnings Calls Transcript Chunks"},
    "filing": {"tier": 1, "weight": 1.0, "label": "Tier 1: Regulatory Filing", "description": "Official Exchange & Regulatory Filings"},
    
    "investor presentation": {"tier": 2, "weight": 0.85, "label": "Tier 2: Investor Presentation", "description": "Company Investor Deck Presentations"},
    "company release": {"tier": 2, "weight": 0.85, "label": "Tier 2: Company Release", "description": "Official Corporate Announcements & Press Releases"},
    "press release": {"tier": 2, "weight": 0.85, "label": "Tier 2: Press Release", "description": "Official Corporate Announcements & Press Releases"},
    "research report": {"tier": 2, "weight": 0.85, "label": "Tier 2: Research Report", "description": "Professional Sell-side Research Reports"},
    
    "news": {"tier": 3, "weight": 0.65, "label": "Tier 3: News Source", "description": "Verified Financial News Outlets (e.g. Bloomberg, Economic Times)"},
    "alert": {"tier": 3, "weight": 0.65, "label": "Tier 3: Smart Alert", "description": "MarketBeacon Generated Intelligent Alert"},
    "daily briefing": {"tier": 3, "weight": 0.65, "label": "Tier 3: Daily Briefing", "description": "MarketBeacon AI Daily Summary Briefing"},
    
    "social": {"tier": 4, "weight": 0.40, "label": "Tier 4: Social Source", "description": "Unverified Social Media Posts and Commentary"},
    "twitter": {"tier": 4, "weight": 0.40, "label": "Tier 4: Twitter Feed", "description": "Real-time Twitter Scrapes"},
    "notification": {"tier": 4, "weight": 0.40, "label": "Tier 4: Watchlist Alert", "description": "Watchlist Keyword Trigger Alert Notification"}
}


def get_source_tier_info(doc_type: str, source_label: str = "") -> dict:
    """
    Looks up the trust tier and source quality weight based on the document type
    or source label.
    """
    dt = (doc_type or "").strip().lower()
    sl = (source_label or "").strip().lower()
    
    # Check keys directly
    for key, info in SOURCE_TIER_MAPPING.items():
        if key in dt or key in sl:
            return info
            
    # Conditional keyword lookups
    if "report" in dt or "report" in sl:
        return SOURCE_TIER_MAPPING["annual report"]
    if "presentation" in dt or "presentation" in sl:
        return SOURCE_TIER_MAPPING["investor presentation"]
    if "news" in dt or "news" in sl:
        return SOURCE_TIER_MAPPING["news"]
    if "twitter" in dt or "tweet" in dt or "twitter" in sl or "tweet" in sl:
        return SOURCE_TIER_MAPPING["twitter"]
        
    # Standard general fallback
    return {
        "tier": 3,
        "weight": 0.60,
        "label": "Tier 3: External Source",
        "description": "General External Information Sources"
    }
