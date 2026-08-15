import logging
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# SIMULATED DATA NOTICE
#
# LocalFinancialDataProvider returns ILLUSTRATIVE, NON-LIVE figures. They are not
# sourced from company filings, exchanges, or any market data vendor, and they do
# not update.
#
# These values previously carried fabricated attributions such as
# "NVIDIA FY26 Form 10-K" with specific filing dates, which presented invented
# numbers as if they came from real regulatory documents. Those attributions have
# been removed.
#
# Every payload now carries `is_simulated: True` and `data_source`, and the
# frontend renders a "SIMULATED" badge wherever these values are displayed.
# Replacing this with a live provider is tracked separately (P1).
# ─────────────────────────────────────────────────────────────────────────────

SIMULATED_SOURCE_LABEL = "Simulated sample data - not from company filings"
SIMULATED_PROVIDER_NAME = "LocalFinancialDataProvider (simulated)"

# Standard company alias map for normalization
COMPANIES_MAP = {
    "hdfc bank": "HDFC Bank",
    "hdfcbank": "HDFC Bank",
    "hdfc": "HDFC Bank",
    "tata consultancy services": "TCS",
    "tcs": "TCS",
    "infosys": "Infosys",
    "reliance": "Reliance Industries",
    "reliance industries": "Reliance Industries",
    "nvidia": "Nvidia",
    "tesla": "Tesla",
    "tata motors": "Tata Motors",
    "tata": "Tata Motors",
    "sbi": "SBI",
    "state bank of india": "SBI"
}


def normalize_company_name(name: str) -> str:
    """
    Normalizes company name using the alias map.
    Handles capitalization, spacing, and substring matching.
    """
    if not name:
        return ""
    
    name_clean = name.strip().lower()
    
    # Check exact match
    if name_clean in COMPANIES_MAP:
        return COMPANIES_MAP[name_clean]
        
    # Check substring inclusion, sorted by key length descending to find longest matches first
    sorted_keys = sorted(COMPANIES_MAP.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in name_clean:
            return COMPANIES_MAP[key]
            
    # Default fallback: title case
    return name.strip().title()


class FinancialDataProvider(ABC):
    """
    Abstract Base Class defining the contract for financial data integration.
    """
    
    @abstractmethod
    def get_company_fundamentals(self, company_name: str) -> dict:
        """
        Retrieve structured fundamentals for a given company.
        Returns a dictionary containing metrics:
        - revenue
        - profit
        - roe
        - debt
        - cash_flow
        - market_cap
        - pe_ratio
        - pb_ratio
        - revenue_growth
        - profit_growth
        - source_document
        - source_date
        - freshness_date
        """
        pass


class LocalFinancialDataProvider(FinancialDataProvider):
    """
    Offline placeholder provider.

    WARNING: these figures are SIMULATED sample values used so the UI has
    something to render. They are illustrative only, are not live, and are not
    taken from company filings or any market data source. Do not rely on them.
    """

    def __init__(self):
        # Simulated sample fundamentals (NOT sourced from filings).
        self._db = {
            "TCS": {
                "company_name": "TCS",
                "revenue": "₹2.45T",
                "profit": "₹640B",
                "roe": "38.5%",
                "debt": "Low (D/E: 0.03)",
                "cash_flow": "₹450B",
                "market_cap": "₹12.8T",
                "pe_ratio": "28.5x",
                "pb_ratio": "10.2x",
                "revenue_growth": "12.5% YoY",
                "profit_growth": "10.2% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "Infosys": {
                "company_name": "Infosys",
                "revenue": "₹1.85T",
                "profit": "₹450B",
                "roe": "31.2%",
                "debt": "None (D/E: 0.00)",
                "cash_flow": "₹320B",
                "market_cap": "₹8.2T",
                "pe_ratio": "26.8x",
                "pb_ratio": "7.8x",
                "revenue_growth": "9.8% YoY",
                "profit_growth": "8.5% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "HDFC Bank": {
                "company_name": "HDFC Bank",
                "revenue": "₹3.15T",
                "profit": "₹640B",
                "roe": "15.8%",
                "debt": "High (CAR: 18.8%)",
                "cash_flow": "₹850B",
                "market_cap": "₹12.2T",
                "pe_ratio": "18.2x",
                "pb_ratio": "2.5x",
                "revenue_growth": "16.8% YoY",
                "profit_growth": "18.5% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "Reliance Industries": {
                "company_name": "Reliance Industries",
                "revenue": "₹9.80T",
                "profit": "₹720B",
                "roe": "9.5%",
                "debt": "Medium (D/E: 0.38)",
                "cash_flow": "₹1.25T",
                "market_cap": "₹19.5T",
                "pe_ratio": "27.2x",
                "pb_ratio": "2.3x",
                "revenue_growth": "11.2% YoY",
                "profit_growth": "8.2% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "Nvidia": {
                "company_name": "Nvidia",
                "revenue": "$96.3B",
                "profit": "$53.0B",
                "roe": "115.6%",
                "debt": "Low (D/E: 0.12)",
                "cash_flow": "$39.2B",
                "market_cap": "$3.20T",
                "pe_ratio": "62.5x",
                "pb_ratio": "42.8x",
                "revenue_growth": "262% YoY",
                "profit_growth": "282% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "Tesla": {
                "company_name": "Tesla",
                "revenue": "$96.8B",
                "profit": "$15.0B",
                "roe": "18.2%",
                "debt": "Low (D/E: 0.08)",
                "cash_flow": "$13.5B",
                "market_cap": "$820B",
                "pe_ratio": "54.6x",
                "pb_ratio": "12.2x",
                "revenue_growth": "18.8% YoY",
                "profit_growth": "14.5% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "Wipro": {
                "company_name": "Wipro",
                "revenue": "₹910B",
                "profit": "₹120B",
                "roe": "15.4%",
                "debt": "Low (D/E: 0.12)",
                "cash_flow": "₹140B",
                "market_cap": "₹2.6T",
                "pe_ratio": "21.5x",
                "pb_ratio": "3.2x",
                "revenue_growth": "4.2% YoY",
                "profit_growth": "3.5% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "ICICI Bank": {
                "company_name": "ICICI Bank",
                "revenue": "₹1.95T",
                "profit": "₹410B",
                "roe": "17.4%",
                "debt": "High (CAR: 18.2%)",
                "cash_flow": "₹420B",
                "market_cap": "₹8.1T",
                "pe_ratio": "19.5x",
                "pb_ratio": "3.1x",
                "revenue_growth": "14.2% YoY",
                "profit_growth": "16.8% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "Axis Bank": {
                "company_name": "Axis Bank",
                "revenue": "₹1.25T",
                "profit": "₹250B",
                "roe": "16.2%",
                "debt": "High (CAR: 17.5%)",
                "cash_flow": "₹280B",
                "market_cap": "₹3.8T",
                "pe_ratio": "15.2x",
                "pb_ratio": "2.2x",
                "revenue_growth": "12.8% YoY",
                "profit_growth": "14.2% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "SBI": {
                "company_name": "SBI",
                "revenue": "₹4.10T",
                "profit": "₹610B",
                "roe": "14.5%",
                "debt": "High (CAR: 16.5%)",
                "cash_flow": "₹920B",
                "market_cap": "₹6.8T",
                "pe_ratio": "11.2x",
                "pb_ratio": "1.5x",
                "revenue_growth": "10.5% YoY",
                "profit_growth": "12.2% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "AMD": {
                "company_name": "AMD",
                "revenue": "$22.6B",
                "profit": "$850M",
                "roe": "1.5%",
                "debt": "Low (D/E: 0.04)",
                "cash_flow": "$2.1B",
                "market_cap": "$255B",
                "pe_ratio": "300x",
                "pb_ratio": "4.5x",
                "revenue_growth": "12.2% YoY",
                "profit_growth": "-15% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "Intel": {
                "company_name": "Intel",
                "revenue": "$54.2B",
                "profit": "$1.2B",
                "roe": "1.8%",
                "debt": "Medium (D/E: 0.42)",
                "cash_flow": "$9.5B",
                "market_cap": "$135B",
                "pe_ratio": "112x",
                "pb_ratio": "1.4x",
                "revenue_growth": "-14% YoY",
                "profit_growth": "-78% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "TSMC": {
                "company_name": "TSMC",
                "revenue": "$69.4B",
                "profit": "$26.8B",
                "roe": "28.5%",
                "debt": "Low (D/E: 0.15)",
                "cash_flow": "$32.5B",
                "market_cap": "$720B",
                "pe_ratio": "26.8x",
                "pb_ratio": "6.8x",
                "revenue_growth": "18.5% YoY",
                "profit_growth": "16.2% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            },
            "BYD": {
                "company_name": "BYD",
                "revenue": "$85.2B",
                "profit": "$4.2B",
                "roe": "22.4%",
                "debt": "Medium (D/E: 0.45)",
                "cash_flow": "$11.2B",
                "market_cap": "$98B",
                "pe_ratio": "23.3x",
                "pb_ratio": "4.8x",
                "revenue_growth": "38.5% YoY",
                "profit_growth": "32.2% YoY",
                "source_document": SIMULATED_SOURCE_LABEL,
                "source_date": None,
                "freshness_date": None
            }
        }
        
    def get_company_fundamentals(self, company_name: str) -> dict:
        normalized = normalize_company_name(company_name)
        if normalized in self._db:
            logger.info(f"[LocalFinancialDataProvider] Returning SIMULATED fundamentals for: {normalized}")
            # Copy so callers cannot mutate the shared table, and tag the payload
            # so every consumer (and the UI) can see this is not real data.
            data = dict(self._db[normalized])
            data["is_simulated"] = True
            data["data_source"] = SIMULATED_PROVIDER_NAME
            return data

        logger.warning(f"[LocalFinancialDataProvider] No fundamentals available for: {normalized}")
        # Structured empty payload. No invented numbers, no invented sources.
        return {
            "company_name": normalized,
            "revenue": "N/A",
            "profit": "N/A",
            "roe": "N/A",
            "debt": "N/A",
            "cash_flow": "N/A",
            "market_cap": "N/A",
            "pe_ratio": "N/A",
            "pb_ratio": "N/A",
            "revenue_growth": "N/A",
            "profit_growth": "N/A",
            "source_document": "Not available",
            "source_date": None,
            "freshness_date": None,
            "is_simulated": True,
            "data_source": SIMULATED_PROVIDER_NAME,
        }


# Global active provider reference
_ACTIVE_PROVIDER = LocalFinancialDataProvider()


def get_financial_provider() -> FinancialDataProvider:
    """
    Factory function returning the active FinancialDataProvider.
    Can be easily configured to return YahooFinance, AlphaVantage, or Polygon providers.
    """
    global _ACTIVE_PROVIDER
    return _ACTIVE_PROVIDER
