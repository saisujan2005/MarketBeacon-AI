import json
import logging
from app.rag.llm_service import ask_llm

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """Attempt to extract and parse JSON from LLM output, handling markdown blocks."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()
    return json.loads(text)


def normalize_confidence(val) -> float:
    """Normalize confidence score to be between 0.0 and 1.0."""
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


def predict_market_impact(
    title: str,
    summary: str = "",
    importance_score: int = 50,
    sentiment: str = "NEUTRAL",
    entities: dict = None
) -> dict:
    """
    Predicts the market price direction impact of financial news.
    Returns: { "predicted_direction": "UP|DOWN|NEUTRAL", "confidence": float, "reasoning": str }
    """
    if not title:
        return {"predicted_direction": "NEUTRAL", "confidence": 0.5, "reasoning": "Empty title"}

    prompt = f"""You are a financial prediction engine.
Predict the immediate direction of relevant asset prices or indices based on this news.

Direction Options:
- UP: Positive price movement likely.
- DOWN: Negative price movement likely.
- NEUTRAL: Little or no price movement expected.

Return ONLY a valid JSON object in this exact format:
{{
  "predicted_direction": "UP|DOWN|NEUTRAL",
  "confidence": 0.0,
  "reasoning": "short justification under 30 words"
}}

News Title:
{title}

News Summary:
{summary or 'No summary provided.'}

Importance Score:
{importance_score}

Sentiment Classification:
{sentiment}

Entities Extracted:
{json.dumps(entities or {{}})}"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM Prediction attempt {attempt + 1} for: {title}")
            response = ask_llm(prompt)
            data = extract_json(response)

            direction = data.get("predicted_direction", "NEUTRAL").upper()
            if direction not in ["UP", "DOWN", "NEUTRAL"]:
                direction = "NEUTRAL"

            raw_conf = data.get("confidence", 0.5)
            confidence = normalize_confidence(raw_conf)

            reasoning = data.get("reasoning", "")

            return {
                "predicted_direction": direction,
                "confidence": confidence,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.warning(f"LLM Prediction failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                logger.error("All LLM prediction retries failed, returning NEUTRAL.")
                return {
                    "predicted_direction": "NEUTRAL",
                    "confidence": 0.5,
                    "reasoning": f"Fallback: Prediction failed due to LLM error. Error: {e}"
                }
