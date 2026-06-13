EVENT_TYPES = {

    # Market Flow
    "fpi": "MARKET_FLOW",
    "foreign portfolio": "MARKET_FLOW",

    # Monetary Policy
    "rbi": "MONETARY_POLICY",
    "repo rate": "MONETARY_POLICY",

    # Commodities
    "oil": "COMMODITY",
    "crude": "COMMODITY",
    "brent": "COMMODITY",
    "gold": "COMMODITY",
    "silver": "COMMODITY",

    # IPO
    "ipo": "IPO",

    # Corporate
    "layoff": "CORPORATE",
    "layoffs": "CORPORATE",
    "workforce": "CORPORATE",

    # Regulation
    "sebi": "REGULATION",
    "eu ruling": "REGULATION",
    "regulation": "REGULATION",

    # Earnings
    "earnings": "EARNINGS",
    "profit": "EARNINGS"
}


def detect_event(title):

    title = title.lower()

    for keyword, event_type in EVENT_TYPES.items():

        if keyword in title:
            return event_type

    return "OTHER"