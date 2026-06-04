import os
import unittest
from unittest.mock import patch

from automation_scheduler.oxylabs_web_scraper_api_adapter import OxylabsWebScraperApiAdapter


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b'{"ok":true,"html":"<html>ok</html>"}'


class TestOxylabsWebScraperApiAdapter(unittest.TestCase):
    def test_disabled_by_default(self):
        adapter = OxylabsWebScraperApiAdapter(source_id="official_nfl_staff_or_news_pages", domain="nfl.com")
        decision = adapter.evaluate()
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["blocked_reason"], "oxylabs_disabled_by_default")
        self.assertEqual(decision["paid_source_enabled_count"], 0)

    def test_source_allowlist_rejects_unapproved_sources(self):
        adapter = OxylabsWebScraperApiAdapter(
            source_id="open_github_coaching_dataset",
            domain="nfl.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
        )
        decision = adapter.evaluate()
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["blocked_reason"], "source_id_not_allowlisted")

    def test_blocklist_rejects_fangraphs_even_when_enabled(self):
        adapter = OxylabsWebScraperApiAdapter(
            source_id="official_team_press_releases",
            domain="fangraphs.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
        )
        decision = adapter.evaluate()
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["blocked_reason"], "domain_blocklisted")

    def test_allowed_path_fetches_text_without_persisting_raw_html(self):
        adapter = OxylabsWebScraperApiAdapter(
            source_id="official_nfl_staff_or_news_pages",
            domain="nfl.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
        )
        with patch.dict(
            os.environ,
            {
                "OXYLABS_API_USERNAME": "user",
                "OXYLABS_API_PASSWORD": "pass",
                "OXYLABS_API_ENDPOINT": "https://api.example.com/scrape",
            },
            clear=False,
        ), patch(
            "automation_scheduler.oxylabs_web_scraper_api_adapter.urllib.request.urlopen",
            return_value=_FakeResponse(),
        ):
            response = adapter.fetch_text("https://www.nfl.com/")
        self.assertTrue(response["ok"])
        self.assertEqual(response["status"], "ok")
        self.assertIn('"html":"<html>ok</html>"', response["text"])
        self.assertFalse(response["raw_html_persisted"])
        self.assertFalse(response["raw_payload_included"])
        self.assertFalse(response["secrets_included"])

    def test_not_configured_blocks_without_network(self):
        adapter = OxylabsWebScraperApiAdapter(
            source_id="official_nfl_staff_or_news_pages",
            domain="nfl.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
        )
        with patch.dict(os.environ, {}, clear=True):
            response = adapter.fetch_text("https://www.nfl.com/")
        self.assertFalse(response["ok"])
        self.assertEqual(response["blocked_reason"], "oxylabs_web_scraper_not_configured")
        self.assertFalse(response["raw_html_persisted"])


if __name__ == "__main__":
    unittest.main()
