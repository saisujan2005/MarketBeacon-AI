"""
Unit tests for the local AI engines: FinBERT, spaCy NER, sector classifier,
and the rule-based local importance scoring system.

Run with:
    python -m unittest app.test_ai_upgrades
"""

import unittest
from unittest.mock import patch, MagicMock

from app.agents.sector_classifier import classify_sector
from app.agents.importance_scorer import calculate_importance
from app.agents.finbert_sentiment import analyze_sentiment_local
from app.agents.spacy_entity_extractor import extract_entities_local


class TestLocalIntelligenceUpgrades(unittest.TestCase):

    def test_sector_classification(self):
        """Verify that rule-based sector classifier maps key terms properly."""
        res_bank = classify_sector("RBI to review commercial bank repo rates")
        self.assertEqual(res_bank["sector"], "Banking")
        self.assertTrue(res_bank["confidence"] >= 50)

        res_it = classify_sector("TCS and Infosys report new cloud AI software solutions")
        self.assertEqual(res_it["sector"], "IT")

        res_metals = classify_sector("Tata Steel increases steel output at mining sites")
        self.assertEqual(res_metals["sector"], "Metals")

        res_telecom = classify_sector("Jio expands 5g spectrum connectivity")
        self.assertEqual(res_telecom["sector"], "Telecom")

        res_other = classify_sector("Random news title that does not match any keywords")
        self.assertEqual(res_other["sector"], "OTHER")

    def test_local_importance_calculation(self):
        """Verify that local importance scorer aggregates trigger adjustments."""
        # MONETARY_POLICY base is 95
        score, level = calculate_importance(
            title="RBI announces unexpected rate cut of 25bps",
            content="MPC voted on cuts.",
            event_type="MONETARY_POLICY",
            sentiment="BULLISH",
            sentiment_conf=0.9
        )
        self.assertTrue(score >= 95)
        self.assertEqual(level, "CRITICAL")

        # OTHER base is 10, should boost slightly on earnings trigger
        score2, level2 = calculate_importance(
            title="Medium company reports earnings beat",
            content="Profit jumps.",
            event_type="OTHER"
        )
        self.assertEqual(score2, 18)  # 10 + 8
        self.assertEqual(level2, "LOW")

    @patch("app.agents.finbert_sentiment.get_sentiment_pipeline")
    def test_finbert_sentiment_mocked(self, mock_get_pipeline):
        """Verify FinBERT output mapping using a mocked transformers pipeline."""
        mock_nlp = MagicMock()
        mock_nlp.return_value = [{"label": "positive", "score": 0.94}]
        mock_get_pipeline.return_value = mock_nlp

        res = analyze_sentiment_local("Great profit reports", "Net profit jumps.")
        self.assertEqual(res["sentiment"], "BULLISH")
        self.assertAlmostEqual(res["confidence"], 0.94)
        self.assertEqual(res["reasoning"], "Generated from FinBERT")

    @patch("app.agents.spacy_entity_extractor.get_spacy_model")
    def test_spacy_ner_mocked(self, mock_get_nlp):
        """Verify spaCy entity extraction maps labels correctly using a mocked doc."""
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        
        ent1 = MagicMock()
        ent1.text = "Reliance Industries Ltd"
        ent1.label_ = "ORG"
        
        ent2 = MagicMock()
        ent2.text = "Shaktikanta Das"
        ent2.label_ = "PERSON"
        
        ent3 = MagicMock()
        ent3.text = "India"
        ent3.label_ = "GPE"
        
        mock_doc.ents = [ent1, ent2, ent3]
        mock_nlp.return_value = mock_doc
        mock_get_nlp.return_value = mock_nlp

        res = extract_entities_local("Reliance boss Mukesh Ambani reports in India.")
        self.assertIn("Reliance Industries Ltd", res["companies"])
        self.assertIn("Shaktikanta Das", res["people"])
        self.assertIn("India", res["countries"])
        self.assertEqual(res["organizations"], [])  # Corporate suffix matched Ltd -> companies


if __name__ == "__main__":
    unittest.main()
