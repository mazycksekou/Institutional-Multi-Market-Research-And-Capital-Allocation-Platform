import unittest

from automation_scheduler.provider_registry import get_provider_registry, provider_min_interval_seconds
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestProviderRegistry(unittest.TestCase):
    def test_placeholder_providers_exist(self):
        registry = get_provider_registry()
        for provider in [
            "sportsbooks",
            "odds_api",
            "opticodds",
            "sportradar",
            "sportsgameodds",
            "kalshi",
            "alpaca",
            "polygon_or_massive",
            "news_provider",
        ]:
            self.assertIn(provider, registry)
            self.assertTrue(registry[provider]["placeholder_only"])

    def test_rate_limit_floor(self):
        config = get_default_scheduler_config()
        self.assertGreaterEqual(provider_min_interval_seconds("odds_api", config), 3)
