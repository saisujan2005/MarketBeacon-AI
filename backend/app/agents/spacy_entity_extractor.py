import os

logger = logging.getLogger(__name__)

DISABLE_LOCAL_ML = os.getenv("DISABLE_LOCAL_ML", "False").lower() in ("true", "1", "yes")

# Lazy-loaded spaCy model singleton
_nlp = None


def get_spacy_model():
    """Lazy-loads the spaCy NLP model, trying en_core_web_lg first, then en_core_web_sm."""
    global _nlp
    if DISABLE_LOCAL_ML:
        return None
    if _nlp is None:
        try:
            import spacy
        except ImportError:
            logger.error(
                "spaCy is not installed. Entity extraction will return empty arrays. "
                "Run: pip install spacy && python -m spacy download en_core_web_lg"
            )
            return None

        # Try to load large model, then fall back to small model if large is not downloaded
        for model_name in ["en_core_web_lg", "en_core_web_sm"]:
            try:
                logger.info(f"Loading spaCy model '{model_name}' locally...")
                _nlp = spacy.load(model_name)
                logger.info(f"spaCy model '{model_name}' loaded successfully.")
                break
            except OSError:
                logger.warning(f"spaCy model '{model_name}' not found on system.")

        if _nlp is None:
            logger.error("No compatible spaCy models found. Run: python -m spacy download en_core_web_lg")

    return _nlp


def extract_entities_local(text: str) -> dict:
    """
    Extracts organizations, companies, people, and countries from text using local spaCy NER.
    Returns: { "companies": [], "people": [], "countries": [], "organizations": [] }
    """
    default_res = {
        "companies": [],
        "people": [],
        "countries": [],
        "organizations": []
    }

    if not text:
        return default_res

    nlp = get_spacy_model()
    if nlp is None:
        return default_res

    try:
        doc = nlp(text)

        companies = []
        people = []
        countries = []
        organizations = []

        # Corporate suffix matching for separating companies from other orgs
        corp_suffixes = [
            "ltd", "inc", "corp", "group", "bank", "co.", "co ", "plc", 
            "gmbh", "technologies", "motors", "industries", "holdings"
        ]
        known_companies = [
            "reliance", "tcs", "infosys", "wipro", "apple", "google", 
            "microsoft", "amazon", "tesla", "sebi", "rbi", "fed", "facebook", 
            "netflix", "meta", "nvidia", "chevron", "bp", "shell", "aramco"
        ]

        for ent in doc.ents:
            val = ent.text.strip()
            if not val or len(val) < 2:
                continue

            if ent.label_ == "ORG":
                lower_val = val.lower()
                # Check if it looks like a business corporation or known company
                is_company = any(s in lower_val for s in corp_suffixes) or any(k in lower_val for k in known_companies)
                if is_company:
                    companies.append(val)
                else:
                    organizations.append(val)
            elif ent.label_ == "PERSON":
                people.append(val)
            elif ent.label_ == "GPE":
                # GPE handles countries, cities, states
                countries.append(val)

        # Deduplicate, sort, and return
        return {
            "companies": sorted(list(set(companies))),
            "people": sorted(list(set(people))),
            "countries": sorted(list(set(countries))),
            "organizations": sorted(list(set(organizations)))
        }

    except Exception as e:
        logger.error(f"Error performing local spaCy entity extraction: {e}")
        return default_res
