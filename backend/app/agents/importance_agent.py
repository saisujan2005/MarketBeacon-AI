"""
Importance scorer — returns a 0-100 score for a given event type.

Higher score = more important = more likely to trigger an alert.
Alert threshold is 85 (see alert_agent.py).
"""

IMPORTANCE_SCORES = {
    "MONETARY_POLICY": 95,   # RBI/Fed decisions — highest impact
    "GEOPOLITICAL":    92,   # Wars, sanctions, trade wars
    "MARKET_FLOW":     90,   # FPI/FII flows — direct market impact
    "REGULATION":      85,   # SEBI, EU rulings — triggers alert
    "EARNINGS":        85,   # Quarterly results — triggers alert
    "BANKING":         82,   # Bank NPAs, credit events
    "CRYPTO":          80,   # High volatility signals
    "COMMODITY":       80,   # Oil, gold, metals
    "TECH":            75,   # AI, semiconductors, funding
    "IPO":             75,   # IPO listings and activity
    "CORPORATE":       70,   # Mergers, layoffs, leadership
    "REAL_ESTATE":     60,   # Property and REIT news
    "OTHER":           10,   # Not a market event
}


def score_event(event_type: str) -> int:
    """
    Returns importance score (0-100) for a given event type.
    Defaults to 10 for unknown types.
    """
    return IMPORTANCE_SCORES.get(event_type, 10)