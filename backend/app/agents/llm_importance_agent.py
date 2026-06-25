import os
import json
import logging
from app.rag.llm_service import ask_llm
from app.agents.importance_agent import score_event

logger = logging.getLogger(__name__)

# Simple in-memory cache for the duration of the script run
# Maps (title) -> dict of scoring results
_score_cache = {}

def extract_json(text: str) -> dict:
    """Attempt to extract and parse JSON from LLM output, handling markdown blocks."""
    # Find JSON block if wrapped in markdown
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
        
    text = text.strip()
    return json.loads(text)

def score_market_impact(title: str, summary: str = "", event_type: str = "") -> dict:
    """
    Scores the market impact of an article using Groq LLM.
    Returns a dict with importance_score, impact_level, reasoning, confidence, affected_assets.
    Falls back to hardcoded scores if LLM fails.
    """
    if not title:
        return _fallback_score(title, event_type)
        
    cache_key = title.strip().lower()
    if cache_key in _score_cache:
        logger.info(f"Using cached score for: {title}")
        return _score_cache[cache_key]

    prompt = f"""You are an expert financial analyst.

Analyze the provided financial news article and estimate its potential impact on financial markets.

Consider:
1. Economic significance
2. Company significance
3. Sector-wide impact
4. Market-moving potential
5. Urgency
6. Investor relevance

Return ONLY valid JSON in this exact format:
{{
  "importance_score": 0,
  "impact_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "reasoning": "short explanation under 50 words",
  "affected_assets": ["stocks", "bonds", "forex", "crypto"],
  "confidence": 0
}}

News Title:
{title}

News Summary:
{summary or 'No summary provided.'}

Event Type:
{event_type or 'Unknown'}"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM Scoring attempt {attempt + 1} for: {title}")
            response = ask_llm(prompt)
            data = extract_json(response)
            
            # Validate required fields
            if not isinstance(data.get("importance_score"), int) or not (1 <= data["importance_score"] <= 100):
                raise ValueError("Invalid importance_score")
            if not isinstance(data.get("confidence"), int) or not (1 <= data["confidence"] <= 100):
                raise ValueError("Invalid confidence")
            if data.get("impact_level") not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                raise ValueError("Invalid impact_level")
                
            # Ensure affected_assets is a list
            if not isinstance(data.get("affected_assets"), list):
                data["affected_assets"] = []
                
            _score_cache[cache_key] = data
            return data
            
        except Exception as e:
            logger.warning(f"LLM scoring failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                logger.error("All LLM retries failed, falling back to basic scorer.")
                return _fallback_score(title, event_type)

def _fallback_score(title: str, event_type: str) -> dict:
    """Fallback logic using the original hardcoded rule-based system."""
    base_score = score_event(event_type)
    
    if base_score >= 90:
        impact = "CRITICAL"
    elif base_score >= 75:
        impact = "HIGH"
    elif base_score >= 50:
        impact = "MEDIUM"
    else:
        impact = "LOW"
        
    result = {
        "importance_score": base_score,
        "impact_level": impact,
        "reasoning": f"Scored via fallback rule-based system due to LLM timeout/failure. Event type: {event_type}",
        "affected_assets": ["stocks"],
        "confidence": 50
    }
    
    _score_cache[title.strip().lower() if title else ""] = result
    return result
