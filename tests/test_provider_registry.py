import os
import unittest
from automation_scheduler.provider_registry import get_provider_registry


class TestProviderRegistry(unittest.TestCase):
    def setUp(self):
        os.environ.pop("SHARP_PROVIDER_ENABLED", None)
        os.environ.pop("SHARP_LIVE_READS_ENABLED", None)

    def test_placeholder_only(self):
        r = get_provider_registry()
        for key in ["sportsbook_placeholder", "player_props_placeholder", "kalshi_placeholder", "stock_placeholder", "news_placeholder"]:
            self.assertIn(key, r)
            self.assertFalse(r[key]["enabled"])
            self.assertNotIn("api_key", str(r[key]).lower())
            self.assertIn("contract_status", r[key])
            self.assertIn("capabilities", r[key])

    def test_sharp_flags_default_to_disabled(self):
        sharp = get_provider_registry()["sharp_sportsbook"]
        self.assertFalse(sharp["enabled"])
        self.assertFalse(sharp["live_calls_enabled"])

    def test_sharp_provider_enabled_flag_controls_metadata(self):
        os.environ["SHARP_PROVIDER_ENABLED"] = "true"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "on"
        sharp = get_provider_registry()["sharp_sportsbook"]
        self.assertTrue(sharp["enabled"])
        self.assertTrue(sharp["live_calls_enabled"])

    def test_sharp_provider_parses_truthy_values(self):
        for value in ("1", "yes", "on", "true"):
            os.environ["SHARP_PROVIDER_ENABLED"] = value
            os.environ["SHARP_LIVE_READS_ENABLED"] = value
            sharp = get_provider_registry()["sharp_sportsbook"]
            self.assertTrue(sharp["enabled"])
            self.assertTrue(sharp["live_calls_enabled"])
