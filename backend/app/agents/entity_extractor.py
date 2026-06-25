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


def extract_entities(title: str, content: str = "") -> dict:
    """
    Extracts key entities (companies, people, countries, sectors, assets) from financial news.
    Returns: { "companies": [], "people": [], "countries": [], "sectors": [], "assets": [] }
    """
    default_res = {
        "companies": [],
        "people": [],
        "countries": [],
        "sectors": [],
        "assets": []
    }

    if not title:
        return default_res

    prompt = f"""You are a financial news entity extractor.
Extract all relevant named entities from the following financial news item.

Extract:
1. companies: Names of corporations, firms, banks (e.g. "Reliance", "TCS", "RBI", "Federal Reserve", "Apple").
2. people: Names of executives, politicians, central bankers (e.g. "Shaktikanta Das", "Elon Musk").
3. countries: Geographic nations involved (e.g. "India", "United States", "United Kingdom").
4. sectors: Industrial sectors (e.g. "Energy", "Banking", "IT", "Pharma", "Auto", "FMCG", "Real Estate").
5. assets: Mentioned financial assets or asset classes (e.g. "Gold", "Oil", "Nifty 50", "Bitcoin", "Bonds").

Return ONLY a valid JSON object in this exact format:
{{
  "companies": ["Name1", "Name2"],
  "people": ["Name1"],
  "countries": ["Name1"],
  "sectors": ["Name1"],
  "assets": ["Name1"]
}}

Rules:
- Be precise. If a category has no entities, return an empty array [].
- Normalize country names (e.g., "UK" -> "United Kingdom", "US" -> "United States").

News Title:
{title}

News Summary:
{content or 'No summary provided.'}"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM Entity Extraction attempt {attempt + 1} for: {title}")
            response = ask_llm(prompt)
            data = extract_json(response)

            # Standardize keys and ensure they are lists
            extracted = {}
            for key in ["companies", "people", "countries", "sectors", "assets"]:
                items = data.get(key, [])
                if isinstance(items, list):
                    extracted[key] = [str(i).strip() for i in items if i]
                else:
                    extracted[key] = []

            return extracted

        except Exception as e:
            logger.warning(f"LLM Entity Extraction failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                logger.error("All LLM entity extraction retries failed, returning empty entities.")
                return default_res
