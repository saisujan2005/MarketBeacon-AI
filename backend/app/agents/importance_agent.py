"""
Importance scorer — returns a 0-100 score for a given event type.

Higher score = more important = more likely to trigger an alert.
Alert threshold is 85 (see alert_agent.py).
"""

IMPORTANCE_SCORES = {
    "MONETARY_POLICY": 95,   # RBI/Fed decisions — highest impact (95-100)
    "GEOPOLITICAL":    85,   # Wars, sanctions, trade wars
    "MARKET_FLOW":     80,   # FPI/FII flows — direct market impact
    "REGULATION":      75,   # SEBI, EU rulings
    "EARNINGS":        80,   # Quarterly results (80-90)
    "BANKING":         70,   # Bank NPAs, credit events
    "CRYPTO":          65,   # Volatility signals
    "COMMODITY":       65,   # Oil, gold, metals (60-80 range)
    "TECH":            60,   # AI, semiconductors, funding
    "IPO":             70,   # IPO listings and activity
    "CORPORATE":       55,   # Mergers, layoffs, leadership
    "REAL_ESTATE":     45,   # Property and REIT news
    "OTHER":           30,   # General opinion/other articles (20-50 range)
}


def score_event(event_type: str) -> int:
    """
    Returns importance score (0-100) for a given event type.
    Defaults to 10 for unknown types.
    """
    return IMPORTANCE_SCORES.get(event_type, 10)