"""
Dossier Quality Benchmark and Integration Tests.
Targets company dossier generation for TCS, Infosys, HDFC Bank, Reliance, Nvidia, and Tesla.
Asserts correct scorecard formatting, chronological timeline ordering, financial data parity,
and structured citation schemas.

Run with:
    python -m unittest app.test_dossier_quality
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from app.services.research_agent import get_or_generate_company_research, discover_company_peers
from app.services.financial_data import get_financial_provider, normalize_company_name


class TestDossierQuality(unittest.TestCase):

    def setUp(self):
        # Create a mock database session
        self.mock_db = MagicMock()
        
        # Configure mock_db to return None for cached queries (simulate cache miss)
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    def test_alias_normalization(self):
        """Verify alias map normalizes inputs to canonical company names."""
        self.assertEqual(normalize_company_name("tcs"), "TCS")
        self.assertEqual(normalize_company_name("hdfcbank"), "HDFC Bank")
        self.assertEqual(normalize_company_name("hdfc bank"), "HDFC Bank")
        self.assertEqual(normalize_company_name("tesla"), "Tesla")
        self.assertEqual(normalize_company_name("nvidia"), "Nvidia")
        self.assertEqual(normalize_company_name("reliance"), "Reliance Industries")

    @patch("app.services.research_agent.ask_llm")
    def test_peer_discovery_mocked(self, mock_ask_llm):
        """Verify dynamic peer discovery parses LLM response correctly and caches it."""
        mock_ask_llm.return_value = """
        {
            "sector": "Technology",
            "industry": "IT Services",
            "market_cap_range": "Mega-Cap",
            "peers": ["Infosys", "Wipro", "HCL Tech", "Cognizant"]
        }
        """
        peers_data = discover_company_peers(self.mock_db, "TCS")
        self.assertEqual(peers_data["sector"], "Technology")
        self.assertEqual(peers_data["peers"], ["Infosys", "Wipro", "HCL Tech", "Cognizant"])
        # Verify db.add was called to cache
        self.assertTrue(self.mock_db.add.called)
        self.assertTrue(self.mock_db.commit.called)

    @patch("app.services.research_agent.ask_llm")
    @patch("app.services.research_agent.retrieve")
    def test_dossier_generation_tcs(self, mock_retrieve, mock_ask_llm):
        """Test dossier generation for TCS. Asserts scorecard, timelines, peer data parity, and citations."""
        # 1. Mock retriever to return dummy context chunks
        mock_retrieve.return_value = [
            {
                "title": "TCS Q4 Results Announcement",
                "source": "TCS Q4 Report",
                "text": "TCS reported a stellar 12.5% YoY revenue growth. Low debt is a key strength.",
                "similarity_score": 0.85
            }
        ]

        # 2. Mock LLM response with valid JSON matching requested format
        llm_response = {
            "scorecard": {
                "business_quality": {"score": 90, "explanation": "Leading global player with strong moat."},
                "growth": {"score": 85, "explanation": "Growing double digits YoY in key markets."},
                "financial_strength": {"score": 95, "explanation": "Low debt levels and healthy cash flow."},
                "management": {"score": 85, "explanation": "Consistent leadership execution."},
                "risk": {"score": 40, "explanation": "Low risk profile compared to peers."},
                "valuation": {"score": 75, "explanation": "Fairly valued relative to growth outlook."},
                "overall": 80
            },
            "timeline": [
                {"date": "24 Jun 2026", "event": "Released next-gen AI platform.", "impact": "Bullish", "source": "TCS PR"},
                {"date": "15 May 2026", "event": "Secured $1B cloud contract.", "impact": "Bullish", "source": "Regulatory Filing"},
                {"date": "10 Apr 2026", "event": "Slight slowdown in UK markets.", "impact": "Neutral", "source": "Earnings Call"}
            ],
            "peer_comparison": [
                # LLM provides draft peer comparisons; agent will post-process them using real financial data provider.
                {"company": "TCS", "revenue": "₹2.2T", "profit": "₹600B", "market_cap": "₹12.0T", "roe": "35%", "debt": "Low"},
                {"company": "Infosys", "revenue": "₹1.7T", "profit": "₹420B", "market_cap": "₹8.0T", "roe": "30%", "debt": "None"}
            ],
            "dossier": {
                "overview": {
                    "text": "TCS is a global leader in IT services.",
                    "citations": [
                        {"source": "Annual Report FY25", "document": "Annual Report", "date": "2025-06-15", "evidence": "TCS is a leader."}
                    ]
                },
                "business_model": {
                    "text": "Consulting-led IT services model.",
                    "citations": []
                },
                "key_financials": {
                    "text": "Stable revenue streams with 38.5% ROE.",
                    "citations": []
                },
                "risks": {
                    "text": "Macro slowdown and talent attrition.",
                    "citations": []
                },
                "opportunities": {
                    "text": "Generative AI customer pipelines.",
                    "citations": []
                },
                "outlook": {
                    "text": "Positive long-term structural demand.",
                    "citations": []
                }
            },
            "confidence_score": 90
        }
        mock_ask_llm.return_value = json.dumps(llm_response)

        # 3. Trigger generation
        result = get_or_generate_company_research(self.mock_db, "TCS")

        # 4. Assertions on Scorecard
        scorecard = result.get("scorecard", {})
        self.assertIn("business_quality", scorecard)
        self.assertEqual(scorecard["business_quality"]["score"], 90)
        self.assertEqual(scorecard["overall"], 80)

        # 5. Assertions on Timeline (Order verification: Newest to oldest)
        timeline = result.get("timeline", [])
        self.assertEqual(len(timeline), 3)
        dates = [datetime.strptime(event["date"], "%d %b %Y") for event in timeline]
        # Check if dates are in descending order
        self.assertTrue(all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1)))

        # 6. Assertions on Peer Data Parity (Overwritten by LocalFinancialDataProvider)
        peer_comparison = result.get("peer_comparison", [])
        self.assertEqual(len(peer_comparison), 2)
        
        provider = get_financial_provider()
        tcs_verified = provider.get_company_fundamentals("TCS")
        infy_verified = provider.get_company_fundamentals("Infosys")

        tcs_row = next(item for item in peer_comparison if item["company"] == "TCS")
        infy_row = next(item for item in peer_comparison if item["company"] == "Infosys")

        # Check fields match provider exactly
        self.assertEqual(tcs_row["revenue"], tcs_verified["revenue"])
        self.assertEqual(tcs_row["profit"], tcs_verified["profit"])
        self.assertEqual(tcs_row["roe"], tcs_verified["roe"])
        self.assertEqual(tcs_row["debt"], tcs_verified["debt"])
        self.assertEqual(tcs_row["freshness_date"], tcs_verified["freshness_date"])
        
        self.assertEqual(infy_row["revenue"], infy_verified["revenue"])
        self.assertEqual(infy_row["profit"], infy_verified["profit"])
        self.assertEqual(infy_row["roe"], infy_verified["roe"])

        # 7. Assertions on Dossier & Structured Citations
        dossier = result.get("dossier", {})
        self.assertIn("overview", dossier)
        self.assertIn("text", dossier["overview"])
        self.assertIn("citations", dossier["overview"])
        citations = dossier["overview"]["citations"]
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["source"], "Annual Report FY25")

    @patch("app.services.research_agent.ask_llm")
    @patch("app.services.research_agent.retrieve")
    def test_dossier_generation_hdfc_bank(self, mock_retrieve, mock_ask_llm):
        """Test dossier generation for HDFC Bank."""
        mock_retrieve.return_value = []
        llm_response = {
            "scorecard": {
                "business_quality": {"score": 88, "explanation": "Largest private sector bank in India."},
                "growth": {"score": 82, "explanation": "Consistent credit growth post-merger."},
                "financial_strength": {"score": 85, "explanation": "High capitalization and liquidity."},
                "management": {"score": 90, "explanation": "Highly experienced leadership team."},
                "risk": {"score": 50, "explanation": "Credit risks are well managed."},
                "valuation": {"score": 80, "explanation": "Fair valuation multiplier."},
                "overall": 82
            },
            "timeline": [
                {"date": "22 Jun 2026", "event": "Expanded digital branch network.", "impact": "Bullish", "source": "HDFC Press Release"},
                {"date": "18 Apr 2026", "event": "Announced Q4 financial results.", "impact": "Bullish", "source": "Regulatory Filing"}
            ],
            "peer_comparison": [
                {"company": "HDFC Bank", "revenue": "₹3.0T", "profit": "₹600B", "market_cap": "₹12.0T", "roe": "15%", "debt": "High"}
            ],
            "dossier": {
                "overview": {
                    "text": "HDFC Bank is India's leading private bank.",
                    "citations": []
                }
            },
            "confidence_score": 85
        }
        mock_ask_llm.return_value = json.dumps(llm_response)

        result = get_or_generate_company_research(self.mock_db, "hdfc bank")
        
        # Verify normalization to "HDFC Bank"
        self.assertEqual(result["company_name"], "HDFC Bank")

        # Verify peer_comparison post-processing
        peer_comparison = result.get("peer_comparison", [])
        self.assertEqual(len(peer_comparison), 1)
        self.assertEqual(peer_comparison[0]["company"], "HDFC Bank")
        
        provider = get_financial_provider()
        hdfc_verified = provider.get_company_fundamentals("HDFC Bank")
        self.assertEqual(peer_comparison[0]["revenue"], hdfc_verified["revenue"])
        self.assertEqual(peer_comparison[0]["profit"], hdfc_verified["profit"])
        self.assertEqual(peer_comparison[0]["freshness_date"], hdfc_verified["freshness_date"])


if __name__ == "__main__":
    unittest.main()
