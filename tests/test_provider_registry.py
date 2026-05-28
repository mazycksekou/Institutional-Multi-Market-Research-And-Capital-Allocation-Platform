import unittest
from automation_scheduler.provider_registry import get_provider_registry


class TestProviderRegistry(unittest.TestCase):
    def test_placeholder_only(self):
        r = get_provider_registry()
        for key in ["sportsbook_placeholder", "player_props_placeholder", "kalshi_placeholder", "stock_placeholder", "news_placeholder"]:
            self.assertIn(key, r)
            self.assertFalse(r[key]["enabled"])
            self.assertNotIn("api_key", str(r[key]).lower())
