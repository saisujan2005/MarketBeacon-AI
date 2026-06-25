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


def analyze_sentiment(title: str, summary: str = "", event_type: str = "") -> dict:
    """
    Classifies the sentiment of financial news.
    Returns: { "sentiment": "BULLISH|BEARISH|NEUTRAL", "confidence": float, "reasoning": str }
    """
    if not title:
        return {"sentiment": "NEUTRAL", "confidence": 0.5, "reasoning": "Empty title"}

    prompt = f"""You are an expert financial analyst.
Classify the sentiment of the following financial news item.

Sentiment Options:
- BULLISH: Positive news likely to drive asset prices/sectors up.
- BEARISH: Negative news likely to drive asset prices/sectors down.
- NEUTRAL: Routine update, mixed impact, or low importance news.

Return ONLY a valid JSON object in this exact format:
{{
  "sentiment": "BULLISH|BEARISH|NEUTRAL",
  "confidence": 0.0,
  "reasoning": "short description under 30 words"
}}

Examples:
- RBI cuts repo rate -> BULLISH
- Company misses earnings -> BEARISH
- Routine corporate update -> NEUTRAL

News Title:
{title}

News Summary:
{summary or 'No summary provided.'}

Event Type:
{event_type or 'Unknown'}"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM Sentiment analysis attempt {attempt + 1} for: {title}")
            response = ask_llm(prompt)
            data = extract_json(response)

            sentiment = data.get("sentiment", "NEUTRAL").upper()
            if sentiment not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                sentiment = "NEUTRAL"

            raw_conf = data.get("confidence", 0.5)
            confidence = normalize_confidence(raw_conf)

            reasoning = data.get("reasoning", "")

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.warning(f"LLM sentiment analysis failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                logger.error("All LLM sentiment retries failed, returning default NEUTRAL.")
                return {
                    "sentiment": "NEUTRAL",
                    "confidence": 0.5,
                    "reasoning": f"Fallback: Analysis failed due to LLM error. Error: {e}"
                }
