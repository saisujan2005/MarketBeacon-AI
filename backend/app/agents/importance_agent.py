IMPORTANCE_SCORES = {
    "MONETARY_POLICY": 95,
    "MARKET_FLOW": 90,
    "REGULATION": 85,
    "EARNINGS": 85,
    "COMMODITY": 80,
    "IPO": 75,
    "CORPORATE": 70,
    "OTHER": 10
}

def score_event(event_type):

    return IMPORTANCE_SCORES.get(
        event_type,
        10
    )