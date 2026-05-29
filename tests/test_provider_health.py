import unittest
import re

from automation_scheduler.provider_contracts import get_default_provider_contracts
from automation_scheduler.provider_health import summarize_provider_health


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


if __name__ == "__main__":
    unittest.main()
