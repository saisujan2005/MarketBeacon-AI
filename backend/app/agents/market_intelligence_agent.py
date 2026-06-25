import json
import time
import hashlib
import logging
from app.rag.llm_service import ask_llm
from app.agents.importance_agent import score_event

logger = logging.getLogger(__name__)

# Global in-memory cache for processed articles
_market_intelligence_cache = {}


def extract_json(text: str) -> dict:
    """Attempt to extract and parse JSON from LLM output, handling markdown blocks."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()
    return json.loads(text)


def normalize_confidence(val) -> float:
    """
    Normalizes confidence scores:
    - 0 to 1 -> already normalized
    - 1 to 10 -> divide by 10
    - 10 to 100 -> divide by 100
    - Clamped between 0.0 and 1.0.
    """
    try:
        val = float(val)
    except (ValueError, TypeError):
        return 0.5

    if 0.0 <= val <= 1.0:
        pass
    elif 1.0 < val <= 10.0:
        val = val / 10.0
    elif 10.0 < val <= 100.0:
        val = val / 100.0
    else:
        val = 0.5

    return max(0.0, min(1.0, val))


def _get_article_hash(title: str, summary: str) -> str:
    """Generates an MD5 hash representing the article's unique content."""
    raw_str = f"{title.strip().lower()}:{summary.strip().lower()}"
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest()


def _get_fallback_intelligence(title: str, event_type: str, reason: str = "Fallback triggered") -> dict:
    """Compiles safe default fallback values when the LLM service is down/rate-limited."""
    rule_score = score_event(event_type)

    if rule_score >= 90:
        impact = "CRITICAL"
    elif rule_score >= 75:
        impact = "HIGH"
    elif rule_score >= 50:
        impact = "MEDIUM"
    else:
        impact = "LOW"

    return {
        "importance_score": rule_score,
        "impact_level": impact,
        "sentiment": "NEUTRAL",
        "sentiment_confidence": 0.5,
        "sentiment_reasoning": f"Rule-based default. {reason}",
        "entities": {
            "companies": [],
            "people": [],
            "countries": [],
            "sectors": [],
            "assets": []
        },
        "prediction": "NEUTRAL",
        "prediction_confidence": 0.5,
        "prediction_reasoning": f"Rule-based default. {reason}"
    }


def get_market_intelligence(title: str, summary: str = "", event_type: str = "") -> dict:
    """
    Runs combined financial analysis (scoring, sentiment, entities, predictions) in a single LLM call.
    Includes caching, rate-limit check, validation, and exponential backoff (2s, 4s, 8s).
    """
    if not title:
        return _get_fallback_intelligence(title, event_type, "Empty article title")

    # 1. Cache lookup (Fix 7)
    cache_key = _get_article_hash(title, summary)
    if cache_key in _market_intelligence_cache:
        logger.info(f"[CACHE HIT] Loaded market intelligence for: '{title}'")
        return _market_intelligence_cache[cache_key]

    prompt = f"""You are an advanced financial AI system. 
Analyze the provided news item and complete all of the following steps:

1. IMPORTANCE & IMPACT LEVEL: Estimate market relevance from 1-100.
   - 90-100 (CRITICAL): Central bank rate decisions, sovereign defaults, crises.
   - 75-89 (HIGH): Major earnings beats/misses, M&As, regulatory bans.
   - 50-74 (MEDIUM): Medium corporate events, product launches, industry surveys.
   - Under 50 (LOW): Routine corporate announcements, minor partnerships.
   Assign an impact_level matching: LOW (under 50), MEDIUM (50-74), HIGH (75-89), or CRITICAL (90-100).

2. SENTIMENT CLASSIFICATION: Classify news tone as BULLISH, BEARISH, or NEUTRAL.
   Assign a confidence score (0 to 1) and a short reasoning.

3. KEY ENTITY EXTRACTION: Extract companies, people, countries, sectors, and assets.
   - Normalize country names (e.g. "US" -> "United States").

4. MARKET IMPACT PREDICTION: Predict immediate asset price direction as UP, DOWN, or NEUTRAL.
   Assign a direction confidence score (0 to 1) and a short reasoning.

Return ONLY a valid JSON object in this exact format:
{{
  "importance_score": 85,
  "impact_level": "HIGH",
  "sentiment": "BULLISH",
  "sentiment_confidence": 0.9,
  "sentiment_reasoning": "reason for sentiment",
  "entities": {{
    "companies": ["Reliance"],
    "people": [],
    "countries": ["India"],
    "sectors": ["Energy"],
    "assets": ["Bonds"]
  }},
  "prediction": "UP",
  "prediction_confidence": 0.85,
  "prediction_reasoning": "reason for price prediction"
}}

News Title:
{title}

News Summary:
{summary or 'No summary provided.'}

Event Type Hint:
{event_type or 'Unknown'}"""

    # Exponential backoff parameters (Fix 2)
    max_attempts = 3
    wait_times = [2.0, 4.0, 8.0]

    for attempt_idx in range(max_attempts):
        attempt_num = attempt_idx + 1
        try:
            # Query LLM (rate-limiting and circuit breaker are handled inside ask_llm)
            response = ask_llm(prompt, article_title=title, attempt=attempt_num)
            data = extract_json(response)

            # --- Validation layer ---
            # Importance score
            imp_score = data.get("importance_score", 50)
            try:
                imp_score = int(imp_score)
            except (ValueError, TypeError):
                imp_score = 50
            imp_score = max(1, min(100, imp_score))

            # Impact level
            imp_level = data.get("impact_level", "LOW").upper()
            if imp_level not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                if imp_score >= 90:
                    imp_level = "CRITICAL"
                elif imp_score >= 75:
                    imp_level = "HIGH"
                elif imp_score >= 50:
                    imp_level = "MEDIUM"
                else:
                    imp_level = "LOW"

            # Sentiment
            sentiment = data.get("sentiment", "NEUTRAL").upper()
            if sentiment not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                sentiment = "NEUTRAL"

            sent_conf = normalize_confidence(data.get("sentiment_confidence", 0.5))
            sent_reasoning = data.get("sentiment_reasoning", "")

            # Entities
            ent_block = data.get("entities", {})
            cleaned_entities = {}
            for cat in ["companies", "people", "countries", "sectors", "assets"]:
                names = ent_block.get(cat, [])
                if isinstance(names, list):
                    cleaned_entities[cat] = [str(n).strip() for n in names if n]
                else:
                    cleaned_entities[cat] = []

            # Prediction
            prediction = data.get("prediction", "NEUTRAL").upper()
            if prediction not in ["UP", "DOWN", "NEUTRAL"]:
                prediction = "NEUTRAL"

            pred_conf = normalize_confidence(data.get("prediction_confidence", 0.5))
            pred_reasoning = data.get("prediction_reasoning", "")

            # Final sanitized result
            sanitized_result = {
                "importance_score": imp_score,
                "impact_level": imp_level,
                "sentiment": sentiment,
                "sentiment_confidence": sent_conf,
                "sentiment_reasoning": sent_reasoning,
                "entities": cleaned_entities,
                "prediction": prediction,
                "prediction_confidence": pred_conf,
                "prediction_reasoning": pred_reasoning
            }

            # Save in-memory cache
            _market_intelligence_cache[cache_key] = sanitized_result
            return sanitized_result

        except Exception as e:
            logger.warning(
                f"[AGENT WARNING] Attempt {attempt_num} failed for '{title}': {e}"
            )
            if attempt_num < max_attempts:
                wait_sec = wait_times[attempt_idx]
                logger.info(f"Retrying in {wait_sec} seconds...")
                time.sleep(wait_sec)
            else:
                logger.error(
                    f"[AGENT FAILURE] All {max_attempts} LLM attempts failed. "
                    f"Applying default fallback rules for: '{title}'"
                )
                fallback = _get_fallback_intelligence(
                    title, event_type, reason=f"LLM failure on all retries: {e}"
                )
                # Save fallback in cache to prevent immediate retry flooding on same article
                _market_intelligence_cache[cache_key] = fallback
                return fallback
