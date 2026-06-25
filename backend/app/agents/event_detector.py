"""
Event type detector — classifies a news title into a market event category.

Usage:
    from app.agents.event_detector import detect_event
    event_type = detect_event("RBI cuts repo rate by 25bps")
    # -> "MONETARY_POLICY"
"""

EVENT_KEYWORDS = {

    # ── Monetary Policy ───────────────────────────────────────────────────────
    "MONETARY_POLICY": [
        "rbi", "repo rate", "reverse repo", "monetary policy",
        "interest rate", "rate cut", "rate hike", "basis points",
        "bps", "inflation", "cpi", "wpi", "federal reserve", "fed",
        "fomc", "central bank", "liquidity", "crr", "slr",
        "mpc", "quantitative easing", "qe", "tapering",
    ],

    # ── Market Flow ───────────────────────────────────────────────────────────
    "MARKET_FLOW": [
        "fpi", "fii", "foreign portfolio", "foreign institutional",
        "net sellers", "net buyers", "inflows", "outflows",
        "capital flow", "dii", "domestic institutional",
        "bulk deal", "block deal", "mutual fund", "sip",
        "nifty", "sensex", "bse", "nse", "stock market",
        "market rally", "market crash", "sell-off", "selloff",
        "bearish", "bullish", "correction", "rebound",
    ],

    # ── Commodities ───────────────────────────────────────────────────────────
    "COMMODITY": [
        "oil", "crude", "brent", "wti", "opec",
        "gold", "silver", "platinum", "copper", "zinc", "aluminium",
        "natural gas", "commodity", "mcx", "metal",
        "wheat", "corn", "soybean", "sugar", "cotton",
        "rubber", "palm oil", "iron ore", "coal",
    ],

    # ── IPO ───────────────────────────────────────────────────────────────────
    "IPO": [
        "ipo", "initial public offering", "listing", "grey market",
        "gmp", "oversubscribed", "subscription", "allotment",
        "pre-ipo", "sme ipo", "mainboard", "unlisted",
        "public issue", "offer for sale", "ofs",
    ],

    # ── Earnings ──────────────────────────────────────────────────────────────
    "EARNINGS": [
        "earnings", "profit", "revenue", "net profit", "net loss",
        "quarterly results", "q1", "q2", "q3", "q4",
        "ebitda", "pat", "eps", "margin", "guidance",
        "results", "beats estimates", "misses estimates",
        "annual report", "dividend", "buyback",
    ],

    # ── Corporate ─────────────────────────────────────────────────────────────
    "CORPORATE": [
        "layoff", "layoffs", "fired", "job cuts", "workforce reduction",
        "retrenchment", "downsizing", "merger", "acquisition",
        "takeover", "stake sale", "divestment", "restructuring",
        "ceo", "cfo", "cto", "md", "chairman", "resigns", "appointed",
        "bankruptcy", "insolvency", "nclt", "demerger", "spinoff",
        "joint venture", "partnership", "expansion",
    ],

    # ── Regulation ────────────────────────────────────────────────────────────
    "REGULATION": [
        "sebi", "regulation", "eu ruling", "antitrust",
        "penalty", "fine", "ban", "compliance", "audit",
        "investigation", "probe", "lawsuit", "court",
        "government policy", "budget", "tax", "gst",
        "customs duty", "import duty", "export ban",
        "data privacy", "gdpr", "dpdp", "sec", "enforcement",
    ],

    # ── Crypto ────────────────────────────────────────────────────────────────
    "CRYPTO": [
        "bitcoin", "btc", "ethereum", "eth", "crypto",
        "cryptocurrency", "blockchain", "defi", "nft",
        "stablecoin", "usdt", "usdc", "binance", "coinbase",
        "web3", "token", "altcoin", "mining", "wallet",
        "exchange hack", "rug pull",
    ],

    # ── Geopolitical ──────────────────────────────────────────────────────────
    "GEOPOLITICAL": [
        "war", "conflict", "sanction", "tariff", "trade war",
        "geopolitical", "tension", "ceasefire", "nato",
        "ukraine", "russia", "china", "taiwan", "middle east",
        "oil embargo", "supply chain", "export control",
        "g20", "g7", "imf", "world bank",
    ],

    # ── Tech & AI ─────────────────────────────────────────────────────────────
    "TECH": [
        "ai", "artificial intelligence", "machine learning",
        "openai", "chatgpt", "gemini", "llm", "nvidia",
        "semiconductor", "chip", "tsmc", "apple", "google",
        "microsoft", "meta", "amazon", "tesla", "startup",
        "funding", "series a", "series b", "valuation", "unicorn",
    ],

    # ── Banking & Finance ─────────────────────────────────────────────────────
    "BANKING": [
        "bank", "nbfc", "npa", "bad loan", "credit",
        "loan", "deposit", "casa", "npa", "write-off",
        "hdfc", "sbi", "icici", "axis", "kotak",
        "insurance", "lic", "premium", "claim",
        "upi", "payment", "fintech", "neobank",
    ],

    # ── Real Estate ───────────────────────────────────────────────────────────
    "REAL_ESTATE": [
        "real estate", "property", "housing", "realty",
        "reit", "commercial property", "residential",
        "home loan", "mortgage", "construction",
        "rera", "builder", "developer",
    ],

}


import re


def detect_event(title: str) -> str:
    """
    Returns the event type for a given article title.
    Checks all keyword lists in priority order with word boundary matching.
    Falls back to 'OTHER' if no match found.
    """
    if not title:
        return "OTHER"

    title_lower = title.lower()

    for event_type, keywords in EVENT_KEYWORDS.items():
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, title_lower):
                return event_type

    return "OTHER"


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_titles = [
        "RBI cuts repo rate by 25 basis points",
        "FPIs remain net sellers, offload shares worth Rs 4500 crore",
        "Gold may see more correction as Citi cuts price forecast",
        "SpaceX IPO to push Musk past $1 trillion",
        "Meta forced to drop WhatsApp fees in landmark EU ruling",
        "Bitcoin surges past $70,000 on ETF approval",
        "Infosys Q3 results: Net profit beats estimates",
        "Tesla lays off 10% of global workforce",
        "Nvidia crosses $3 trillion market cap on AI boom",
        "Some random lifestyle article about cooking",
    ]

    for title in test_titles:
        print(f"{detect_event(title):20s}  {title}")