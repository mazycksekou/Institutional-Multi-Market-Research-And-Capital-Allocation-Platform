import unittest
from unittest.mock import patch

from automation_scheduler.completed_sports_terms_parser import evaluate_completed_sports_terms


class TestCompletedSportsTermsParser(unittest.TestCase):
    def test_detects_noncommercial_and_no_data_mining(self):
        candidate = {"source_id": "x", "source_domain": "example.com", "terms_url": "https://example.com/terms"}
        text = "Non-commercial use only. Data mining is prohibited. Attribution required."
        with patch(
            "automation_scheduler.completed_sports_terms_parser.fetch_public_page_text",
            return_value={"ok": True, "text": text, "transport": "web_scraper_api"},
        ):
            result = evaluate_completed_sports_terms(candidate)
        self.assertTrue(result["terms_checked"])
        self.assertTrue(result["noncommercial_only"])
        self.assertTrue(result["no_data_mining_clause"])
        self.assertTrue(result["attribution_required"])


if __name__ == "__main__":
    unittest.main()

