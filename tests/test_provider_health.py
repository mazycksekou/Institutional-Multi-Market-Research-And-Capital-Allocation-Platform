import unittest
import re

from src.providers.contracts import get_default_provider_contracts
from src.providers.health import compact_provider_health, summarize_provider_health


class TestProviderHealth(unittest.TestCase):
    def test_compact_health_safe(self):
        contracts = get_default_provider_contracts()
        health = summarize_provider_health(contracts)
        self.assertTrue(health["ok"])
        self.assertIn("provider_count", health)
        self.assertIn("top_provider_statuses", health)
        self.assertLessEqual(len(health["top_provider_statuses"]), 10)
        self.assertNotIn("credentials", str(health).lower())
        text = str(health).lower()
        self.assertIsNone(re.search(r"\block\b", text))
        for banned in ["guaranteed", "risk-free", "sure thing", "can't lose"]:
            self.assertNotIn(banned, text)

    def test_compact_sharp_health_uses_compact_booleans(self):
        contract = {
            "provider_id": "sharp_sportsbook",
            "provider_type": "sportsbook_odds",
            "enabled": True,
            "live_calls_enabled": True,
            "dry_run": True,
            "credential_status": "ok",
            "required_credentials": ["SHARP_API_KEY"],
        }
        health = compact_provider_health(contract, blockers=[])
        self.assertEqual(health["provider_id"], "sharp_sportsbook")
        self.assertTrue(health["enabled"])
        self.assertTrue(health["live_calls_enabled"])
        self.assertIn("dry_run_placeholder", health["blockers"])
        self.assertNotIn("SHARP_API_KEY", str(health))


if __name__ == "__main__":
    unittest.main()
