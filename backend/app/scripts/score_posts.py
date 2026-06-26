"""
Post enrichment scoring pipeline.
Implements:
- Local FinBERT Sentiment Analysis (Phase 1)
- Local spaCy NER Entity Extraction (Phase 2)
- Local Sector Classification (Phase 3)
- Local Importance & Impact level Calculation (Phase 4)
- Conditional LLM Market Prediction (Phase 9): ONLY if score >= 85 or CRITICAL.
- Rule-based Timeline indexing (Phase 4)
"""

import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.post import Post
from app.agents.finbert_sentiment import analyze_sentiment_local
from app.agents.spacy_entity_extractor import extract_entities_local
from app.agents.sector_classifier import classify_sector
from app.agents.importance_scorer import calculate_importance
from app.agents.prediction_agent import predict_market_impact
from app.services.timeline_service import add_timeline_event, is_valid_entity_name

logger = logging.getLogger(__name__)

# Throttling batch limit for prediction calls per run
MAX_PREDICTIONS_PER_RUN = 10


def score_posts(db: Session) -> int:
    """
    Finds all unscored posts (importance_score == None) and processes them locally first.
    Queries Groq LLM for prediction ONLY if the event is high-importance (score >= 85 or CRITICAL).
    """
    unscored = (
        db.query(Post)
        .filter(Post.importance_score == None)  # noqa: E711
        .order_by(Post.posted_at.desc())
        .all()
    )

    if not unscored:
        logger.info("No unscored posts in queue.")
        return 0

    logger.info(f"Ingestion queue: {len(unscored)} unscored posts detected.")

    prediction_calls_made = 0
    total_processed = 0

    for post in unscored:
        logger.info(f"Processing article locally: '{post.title}'")

        # 1. Local Entity Extraction (spaCy NER)
        full_text = f"{post.title}. {post.content or ''}"
        entities = extract_entities_local(full_text)

        # 2. Local Sentiment Analysis (FinBERT)
        sent_res = analyze_sentiment_local(post.title, post.content)
        sentiment = sent_res.get("sentiment", "NEUTRAL")
        sentiment_conf = sent_res.get("confidence", 0.5)
        sentiment_reasoning = sent_res.get("reasoning", "Generated from FinBERT")

        # 3. Local Sector Classification
        sector_res = classify_sector(post.title, post.content)
        classified_sector = sector_res.get("sector", "OTHER")
        sector_conf = sector_res.get("confidence", 50)

        # Inject sector into entities JSON block
        entities["sectors"] = [classified_sector]

        # 4. Local Importance & Impact Level Calculation
        importance_score, impact_level = calculate_importance(
            title=post.title,
            content=post.content or "",
            event_type=post.event_type or "OTHER",
            sentiment=sentiment,
            sentiment_conf=sentiment_conf
        )

        # Apply local metrics to database model
        post.importance_score = importance_score
        post.impact_level = impact_level
        post.sentiment = sentiment
        post.sentiment_confidence = sentiment_conf
        post.sentiment_reasoning = sentiment_reasoning
        post.entities = entities
        post.reasoning = f"Locally processed. Sector: {classified_sector}. Sentiment: {sentiment}."
        post.confidence = int((sentiment_conf + (sector_conf / 100)) / 2 * 100)
        post.affected_assets = entities.get("assets", [])

        # 5. Smart LLM Usage: Conditional Groq Predictions (Phase 9)
        if importance_score >= 85 or impact_level == "CRITICAL":
            if prediction_calls_made < MAX_PREDICTIONS_PER_RUN:
                logger.info(f"🔥 [CRITICAL EVENT] Querying Groq Prediction for: '{post.title}'")
                try:
                    pred_res = predict_market_impact(
                        title=post.title,
                        summary=post.content or "",
                        importance_score=importance_score,
                        sentiment=sentiment,
                        entities=entities
                    )
                    post.predicted_direction = pred_res.get("predicted_direction", "NEUTRAL")
                    post.prediction_confidence = pred_res.get("confidence", 0.5)
                    post.prediction_reasoning = pred_res.get("reasoning", "")
                    prediction_calls_made += 1
                except Exception as e:
                    logger.error(f"Failed to query Groq prediction: {e}")
                    post.predicted_direction = "NEUTRAL"
                    post.prediction_confidence = 0.5
                    post.prediction_reasoning = f"Fallback: prediction query failed: {e}"
            else:
                logger.warning(
                    f"[THROTTLED] Prediction batch limit of {MAX_PREDICTIONS_PER_RUN} hit. "
                    f"Queuing prediction for: '{post.title}'"
                )
                # Apply default temporary metrics so post is saved, but we keep prediction neutral
                post.predicted_direction = "NEUTRAL"
                post.prediction_confidence = 0.5
                post.prediction_reasoning = "Prediction throttled (will run in next batch)."
        else:
            # Low importance news gets neutral predictions without querying Groq
            post.predicted_direction = "NEUTRAL"
            post.prediction_confidence = 0.5
            post.prediction_reasoning = "Skipped prediction: Low importance news."

        # 6. Rule-based Timeline Indexing (Phase 4)
        categories = {
            "companies": "company",
            "people": "person",
            "countries": "country"
        }
        for cat_key, entity_type in categories.items():
            names = entities.get(cat_key, [])
            for name in names:
                name_clean = name.strip()
                if name_clean and is_valid_entity_name(name_clean):
                    add_timeline_event(
                        db=db,
                        entity_name=name_clean,
                        entity_type=entity_type,
                        post_id=post.id,
                        event_date=post.posted_at or post.fetched_at,
                        event_title=post.title,
                        description=post.content[:250] if post.content else ""
                    )

        total_processed += 1
        db.commit()

    logger.info(
        f"score_posts run complete: Processed {total_processed} articles. "
        f"Made {prediction_calls_made} Groq LLM market predictions."
    )
    return total_processed


# ── manual run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        total = score_posts(db)
        print(f"Finished scoring: processed {total} articles.")
    finally:
        db.close()