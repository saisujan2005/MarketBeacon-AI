import logging
from app.agents.importance_agent import score_event

logger = logging.getLogger(__name__)


def calculate_importance(
    title: str,
    content: str = "",
    event_type: str = "OTHER",
    sentiment: str = "NEUTRAL",
    sentiment_conf: float = 0.5
) -> tuple[int, str]:
    """
    Calculates the importance score (1-100) and impact level (LOW|MEDIUM|HIGH|CRITICAL)
    fully locally using base event scoring and title keywords.
    """
    base_score = score_event(event_type)

    title_lower = title.lower() if title else ""
    content_lower = content.lower() if content else ""

    # Adjust score based on key trigger patterns in title
    critical_triggers = [
        "rate cut", "rate hike", "repo rate", "sovereign default", "bankruptcy", 
        "liquidation", "acquisition", "merger", "interest rate", "takeover", 
        "bailout", "sanctions", "tariff", "trade war", "debt default", "insolvency"
    ]
    high_triggers = [
        "profit surges", "profit plunges", "earnings beat", "earnings miss", 
        "revenue jumps", "revenue falls", "ceo resigns", "appoints ceo", 
        "probe", "investigates", "sebi ban", "fine of", "legal dispute"
    ]

    import re

    adjustment = 0
    if any(re.search(r'\b' + re.escape(trigger) + r'\b', title_lower) for trigger in critical_triggers):
        adjustment += 15
    elif any(re.search(r'\b' + re.escape(trigger) + r'\b', title_lower) for trigger in high_triggers):
        adjustment += 8

    # Small boost for high confidence non-neutral sentiment
    if sentiment != "NEUTRAL" and sentiment_conf > 0.8:
        adjustment += 3

    importance_score = max(1, min(100, base_score + adjustment))

    # Map importance score to impact level
    if importance_score >= 90:
        impact_level = "CRITICAL"
    elif importance_score >= 75:
        impact_level = "HIGH"
    elif importance_score >= 50:
        impact_level = "MEDIUM"
    else:
        impact_level = "LOW"

    return importance_score, impact_level
