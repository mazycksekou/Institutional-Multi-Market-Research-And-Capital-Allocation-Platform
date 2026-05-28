import unittest

from automation_scheduler.cadence_controller import choose_next_check_seconds
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestCadenceController(unittest.TestCase):
    def test_high_score_rechecks_faster_than_low_score(self):
        config = get_default_scheduler_config()
        high = choose_next_check_seconds(
            market_type="sports_pregame_main",
            opportunity_score=90,
            provider_name="sportsbooks",
            config=config,
        )
        low = choose_next_check_seconds(
            market_type="sports_pregame_main",
            opportunity_score=56,
            provider_name="sportsbooks",
            config=config,
        )
        self.assertLess(high["next_check_seconds"], low["next_check_seconds"])

    def test_provider_rate_limit_is_respected(self):
        config = get_default_scheduler_config()
        result = choose_next_check_seconds(
            market_type="sports_live",
            opportunity_score=95,
            provider_name="sportsbooks",
            config=config,
        )
        self.assertGreaterEqual(result["next_check_seconds"], result["provider_min_interval_seconds"])
        self.assertTrue(result["not_competitive_for_live"])
