from sqlalchemy.orm import Session
from app.models.post import Post
from collections import defaultdict


def get_event_impact_history(db: Session) -> list:
    """
    Aggregates news count, average importance score, and sentiment distribution grouped by event_type.
    """
    posts = db.query(Post).filter(Post.event_type != None).all()  # noqa: E711
    if not posts:
        return []

    groups = defaultdict(list)
    for p in posts:
        groups[p.event_type].append(p)

    results = []
    for event_type, post_list in groups.items():
        total_importance = sum(p.importance_score for p in post_list if p.importance_score is not None)
        valid_importance_count = sum(1 for p in post_list if p.importance_score is not None)
        avg_score = int(total_importance / valid_importance_count) if valid_importance_count > 0 else 50

        bullish = sum(1 for p in post_list if (p.sentiment or "").upper() == "BULLISH")
        bearish = sum(1 for p in post_list if (p.sentiment or "").upper() == "BEARISH")
        neutral = sum(1 for p in post_list if (p.sentiment or "").upper() == "NEUTRAL" or not p.sentiment)
        total = len(post_list)

        bullish_pct = int((bullish / total) * 100) if total > 0 else 0
        bearish_pct = int((bearish / total) * 100) if total > 0 else 0
        neutral_pct = int((neutral / total) * 100) if total > 0 else 0

        # Dominant sentiment string
        if bullish_pct >= bearish_pct and bullish_pct >= neutral_pct:
            dominant = "Bullish"
        elif bearish_pct >= bullish_pct and bearish_pct >= neutral_pct:
            dominant = "Bearish"
        else:
            dominant = "Neutral"

        results.append({
            "event_type": event_type,
            "average_score": avg_score,
            "dominant_sentiment": dominant,
            "bullish_pct": bullish_pct,
            "bearish_pct": bearish_pct,
            "neutral_pct": neutral_pct,
            "news_count": total
        })

    # Sort by count desc
    return sorted(results, key=lambda x: x["news_count"], reverse=True)
