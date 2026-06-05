import unittest
from unittest.mock import patch

from automation_scheduler.completed_sports_api_docs_parser import evaluate_completed_sports_api_docs


class TestCompletedSportsApiDocsParser(unittest.TestCase):
    def test_detects_docs_and_dictionary(self):
        candidate = {
            "source_id": "x",
            "source_domain": "statsapi.mlb.com",
            "api_docs_url": "https://example.com/docs",
            "data_dictionary_url": "https://example.com/dict",
            "source_url": "https://statsapi.mlb.com/api/v1/schedule",
            "source_type": "public_json_api",
            "primary_transport": "residential_proxy",
            "session_required": False,
            "captcha_required": False,
        }
        with patch(
            "automation_scheduler.completed_sports_api_docs_parser.fetch_public_page_text",
            return_value={"ok": True, "text": "docs", "transport": "web_scraper_api"},
        ), patch(
            "automation_scheduler.completed_sports_api_docs_parser.fetch_public_json",
            return_value={"ok": True, "json_payload": {"ok": True}, "transport": "residential_proxy"},
        ):
            result = evaluate_completed_sports_api_docs(candidate)
        self.assertTrue(result["api_docs_checked"])
        self.assertTrue(result["data_dictionary_checked"])
        self.assertTrue(result["public_api_available"])
        self.assertTrue(result["public_json_available"])


if __name__ == "__main__":
    unittest.main()

