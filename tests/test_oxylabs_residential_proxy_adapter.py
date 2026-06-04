import os
import tempfile
import unittest
from unittest.mock import patch

from automation_scheduler.oxylabs_residential_proxy_adapter import OxylabsResidentialProxyAdapter


class _FakeResponse:
    def __init__(self, text):
        self._text = text

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._text.encode("utf-8")


class _FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, request, timeout=None):
        return self.response


class TestOxylabsResidentialProxyAdapter(unittest.TestCase):
    def test_disabled_by_default(self):
        adapter = OxylabsResidentialProxyAdapter(source_id="official_team_staff_pages", domain="nfl.com")
        decision = adapter.evaluate()
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["blocked_reason"], "oxylabs_disabled_by_default")
        self.assertEqual(decision["paid_source_enabled_count"], 0)

    def test_paid_retrieval_requires_explicit_authorization(self):
        adapter = OxylabsResidentialProxyAdapter(source_id="official_team_staff_pages", domain="nfl.com", allow_oxylabs=True)
        decision = adapter.evaluate()
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["blocked_reason"], "paid_retrieval_not_authorized")

    def test_blocklist_rejects_pro_football_reference_even_when_enabled(self):
        adapter = OxylabsResidentialProxyAdapter(
            source_id="official_team_staff_pages",
            domain="pro-football-reference.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
        )
        decision = adapter.evaluate()
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["blocked_reason"], "domain_blocklisted")

    def test_allowed_path_fetches_text_without_persisting_raw_html(self):
        adapter = OxylabsResidentialProxyAdapter(
            source_id="official_team_staff_pages",
            domain="nfl.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
        )
        env = {
            "OXYLABS_PROXY_HOST": "proxy.example.com",
            "OXYLABS_PROXY_PORT": "1234",
            "OXYLABS_PROXY_USERNAME": "user",
            "OXYLABS_PROXY_PASSWORD": "pass",
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "automation_scheduler.oxylabs_residential_proxy_adapter.urllib.request.build_opener",
            return_value=_FakeOpener(_FakeResponse("<html>ok</html>")),
        ):
            response = adapter.fetch_text("https://www.nfl.com/")
        self.assertTrue(response["ok"])
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["text"], "<html>ok</html>")
        self.assertFalse(response["raw_html_persisted"])
        self.assertFalse(response["raw_payload_included"])
        self.assertFalse(response["secrets_included"])

    def test_not_configured_blocks_without_network(self):
        adapter = OxylabsResidentialProxyAdapter(
            source_id="official_team_staff_pages",
            domain="nfl.com",
            allow_oxylabs=True,
            allow_paid_retrieval=True,
        )
        with patch.dict(os.environ, {}, clear=True):
            response = adapter.fetch_text("https://www.nfl.com/")
        self.assertFalse(response["ok"])
        self.assertEqual(response["blocked_reason"], "oxylabs_proxy_not_configured")
        self.assertFalse(response["raw_html_persisted"])


if __name__ == "__main__":
    unittest.main()
