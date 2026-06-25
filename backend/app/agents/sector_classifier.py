import logging

logger = logging.getLogger(__name__)

SECTOR_KEYWORDS = {
    "Banking": [
        "bank", "rbi", "lending", "credit", "repo", "interest rate", "hdfc", "sbi", 
        "icici", "federal reserve", "fed", "finance", "nbfc", "bad loan", "debt", 
        "monetary policy", "central bank", "liquidity", "deposit", "casa"
    ],
    "IT": [
        "it ", "tech", "software", "tcs", "infosys", "wipro", "cognizant", "accenture", 
        "digital", "ai ", "semiconductor", "computer", "cloud", "developer", "technologies",
        "openai", "chatgpt", "gemini", "llm", "nvidia", "chip", "coding"
    ],
    "Energy": [
        "energy", "oil", "gas", "power", "solar", "petrol", "reliance", "ongc", "coal", 
        "grid", "wind", "electricity", "refinery", "crude", "brent", "wti", "utility"
    ],
    "Pharma": [
        "pharma", "drug", "medicine", "healthcare", "vaccine", "sun pharma", "cipla", 
        "dr. reddy", "clinical", "hospital", "biotech", "medical", "fda"
    ],
    "Auto": [
        "auto", "car", "vehicle", "electric vehicle", "ev ", "tata motors", "mahindra", 
        "maruti", "automobile", "scooter", "truck", "evs", "tesla", "byd"
    ],
    "FMCG": [
        "fmcg", "consumer", "hul ", "itc", "nestle", "britannia", "soap", "food", 
        "beverage", "retail", "grocery", "goods", "toothpaste", "shampoo", "dairy"
    ],
    "Telecom": [
        "telecom", "jio", "airtel", "vodafone", "idea", "5g", "4g", "spectrum", 
        "broadband", "mobile", "connectivity", "telecommunication"
    ],
    "Metals": [
        "metal", "steel", "gold", "silver", "copper", "iron", "aluminium", "zinc", 
        "mining", "tata steel", "jsw", "hindalco", "ore", "nickel", "lead"
    ]
}


def classify_sector(title: str, summary: str = "") -> dict:
    """
    Classifies a news article into one of the 8 key sectors using keyword scoring.
    Title matches are weighted higher than summary matches.
    Returns: { "sector": "Banking|IT|Energy|...", "confidence": int }
    """
    title_lower = title.lower() if title else ""
    summary_lower = summary.lower() if summary else ""

    scores = {}

    for sector, keywords in SECTOR_KEYWORDS.items():
        score = 0
        for kw in keywords:
            # Match in title carries high weight
            if kw in title_lower:
                score += 3
            # Match in summary carries medium weight
            if kw in summary_lower:
                score += 1
        scores[sector] = score

    # Find sector with maximum score
    max_sector = None
    max_score = 0

    for sector, score in scores.items():
        if score > max_score:
            max_score = score
            max_sector = sector

    if max_sector and max_score > 0:
        # Confidence score ranges from 50 to 95 based on keyword strength
        confidence = min(95, 50 + max_score * 5)
        return {
            "sector": max_sector,
            "confidence": confidence
        }

    # Default fallback
    return {
        "sector": "OTHER",
        "confidence": 50
    }
