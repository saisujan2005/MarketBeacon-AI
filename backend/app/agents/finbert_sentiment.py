import logging

logger = logging.getLogger(__name__)

# Lazy-loaded pipeline singleton
_sentiment_pipeline = None


def get_sentiment_pipeline():
    """Lazy-loads the transformers pipeline and ProsusAI/finbert model once."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            from transformers import pipeline
            logger.info("Loading FinBERT sentiment analysis model locally...")
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert"
            )
            logger.info("FinBERT model loaded successfully.")
        except ImportError:
            logger.error(
                "Transformers or torch is not installed. Sentiment analysis will fall back to NEUTRAL. "
                "Run: pip install transformers torch"
            )
            return None
        except Exception as e:
            logger.error(f"Error loading FinBERT model: {e}")
            return None
    return _sentiment_pipeline


def classify_sentiment_keywords(title: str, content: str = "") -> dict:
    """
    Fallback keyword-based sentiment analyzer.
    Analyzes title + content for bullish/bearish indicators.
    """
    text = f"{title or ''} {content or ''}".lower()
    
    bullish_keywords = [
        "rally", "surge", "gain", "rise", "beat", "growth", "jump", "soar", "high",
        "bullish", "recovery", "upward", "optimistic", "expansion", "profit",
        "rate cut", "easing", "inflation cooling", "cooling inflation", "stimulus"
    ]
    bearish_keywords = [
        "crash", "plunge", "drop", "fall", "miss", "decline", "slump", "low",
        "bearish", "recession", "downward", "pessimistic", "contraction", "loss",
        "rate hike", "tightening", "inflation surge", "shock", "selloff"
    ]
    
    bull_count = sum(1 for kw in bullish_keywords if kw in text)
    bear_count = sum(1 for kw in bearish_keywords if kw in text)
    
    if bull_count > bear_count:
        return {
            "sentiment": "BULLISH",
            "confidence": 0.70,
            "reasoning": f"Rule-based fallback: Bullish keywords matched ({bull_count} vs {bear_count})"
        }
    elif bear_count > bull_count:
        return {
            "sentiment": "BEARISH",
            "confidence": 0.70,
            "reasoning": f"Rule-based fallback: Bearish keywords matched ({bear_count} vs {bull_count})"
        }
    else:
        return {
            "sentiment": "NEUTRAL",
            "confidence": 0.50,
            "reasoning": "Rule-based fallback: Neutral or balanced keywords"
        }


def analyze_sentiment_local(title: str, summary: str = "") -> dict:
    """
    Performs local sentiment classification using ProsusAI/finbert.
    Falls back to keyword rules if the local AI model fails or is unavailable.
    """
    nlp = get_sentiment_pipeline()
    if nlp is None:
        logger.warning(f"FinBERT pipeline not loaded; using keyword fallback for: '{title}'")
        return classify_sentiment_keywords(title, summary)

    try:
        text = f"{title}. {summary or ''}".strip()
        # Truncate text to fit typical token limits
        text = text[:512]

        results = nlp(text)
        if not results:
            logger.warning(f"FinBERT returned empty results; using keyword fallback for: '{title}'")
            return classify_sentiment_keywords(title, summary)

        res = results[0]
        label = res["label"].lower()
        score = float(res["score"])

        # Map FinBERT label (positive, negative, neutral) to ours
        label_map = {
            "positive": "BULLISH",
            "negative": "BEARISH",
            "neutral": "NEUTRAL"
        }

        sentiment = label_map.get(label, "NEUTRAL")

        return {
            "sentiment": sentiment,
            "confidence": score,
            "reasoning": f"Generated from FinBERT (confidence: {score:.2f})"
        }

    except Exception as e:
        logger.error(f"Error performing local sentiment classification: {e}. Falling back to keywords.")
        return classify_sentiment_keywords(title, summary)

