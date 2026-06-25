import logging
from sqlalchemy.orm import Session
from app.models.post import Post

logger = logging.getLogger(__name__)

SECTORS = ["Banking", "IT", "Energy", "Pharma", "Auto", "FMCG", "Telecom", "Metals"]

# Keywords mapping for robust sector matching fallback
SECTOR_KEYWORDS = {
    "Banking": ["bank", "rbi", "lending", "credit", "repo", "interest rate", "hdfc", "sbi", "icici", "federal reserve", "fed", "finance", "nbfc", "bad loan", "debt"],
    "IT": ["it ", "tech", "software", "tcs", "infosys", "wipro", "cognizant", "accenture", "digital", "ai ", "semiconductor", "computer", "cloud", "developer", "technologies"],
    "Energy": ["energy", "oil", "gas", "power", "solar", "petrol", "reliance", "ongc", "coal", "grid", "wind", "electricity", "refinery"],
    "Pharma": ["pharma", "drug", "medicine", "healthcare", "vaccine", "sun pharma", "cipla", "dr. reddy", "clinical", "hospital", "biotech"],
    "Auto": ["auto", "car", "vehicle", "electric vehicle", "ev ", "tata motors", "mahindra", "maruti", "automobile", "scooter", "truck", "evs"],
    "FMCG": ["fmcg", "consumer", "hul ", "itc", "nestle", "britannia", "soap", "food", "beverage", "retail", "grocery", "goods"],
    "Telecom": ["telecom", "jio", "airtel", "vodafone", "idea", "5g", "4g", "spectrum", "broadband", "mobile", "connectivity", "telecommunication"],
    "Metals": ["metal", "steel", "gold", "silver", "copper", "iron", "aluminium", "zinc", "mining", "tata steel", "jsw", "hindalco", "ore", "nickel", "lead"]
}


def get_sector_intelligence(db: Session) -> list:
    """
    Aggregates news count, average importance score, and average sentiment per sector.
    """
    posts = db.query(Post).all()
    results = []

    for sector in SECTORS:
        sector_posts = []
        kws = SECTOR_KEYWORDS.get(sector, [])

        for post in posts:
            title = (post.title or "").lower()
            content = (post.content or "").lower()
            is_matched = False

            # 1. Match via extracted entities
            if post.entities and isinstance(post.entities.get("sectors"), list):
                extracted_sectors = [s.strip().lower() for s in post.entities["sectors"]]
                if sector.lower() in extracted_sectors:
                    is_matched = True

            # 2. Fallback: match via keywords
            if not is_matched:
                for kw in kws:
                    if kw in title or kw in content:
                        is_matched = True
                        break

            if is_matched:
                sector_posts.append(post)

        news_count = len(sector_posts)
        if news_count == 0:
            results.append({
                "sector": sector,
                "sentiment": "Neutral",
                "score": 50,
                "news_count": 0
            })
            continue

        # Aggregate importance score
        total_importance = sum(p.importance_score for p in sector_posts if p.importance_score is not None)
        valid_importance_count = sum(1 for p in sector_posts if p.importance_score is not None)
        avg_score = int(total_importance / valid_importance_count) if valid_importance_count > 0 else 50

        # Aggregate sentiment
        # BULLISH = 1, NEUTRAL = 0, BEARISH = -1
        sentiment_values = []
        for p in sector_posts:
            sent = (p.sentiment or "NEUTRAL").upper()
            if sent == "BULLISH":
                sentiment_values.append(1)
            elif sent == "BEARISH":
                sentiment_values.append(-1)
            else:
                sentiment_values.append(0)

        avg_sentiment_val = sum(sentiment_values) / len(sentiment_values)

        if avg_sentiment_val > 0.15:
            sentiment_str = "Bullish"
        elif avg_sentiment_val < -0.15:
            sentiment_str = "Bearish"
        else:
            sentiment_str = "Neutral"

        results.append({
            "sector": sector,
            "sentiment": sentiment_str,
            "score": avg_score,
            "news_count": news_count
        })

    return results
