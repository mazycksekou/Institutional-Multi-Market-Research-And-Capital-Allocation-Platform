import unittest
from src.services.streamlit_dashboard_facade import choose_next_check_seconds
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestCadenceController(unittest.TestCase):
    def test_fast_and_slow(self):
        c = get_default_scheduler_config()
        high = choose_next_check_seconds(market_type="sports_pregame_main", opportunity_score=95, provider_name="sportsbook_placeholder", config=c)
        low = choose_next_check_seconds(market_type="low_liquidity", opportunity_score=60, provider_name="sportsbook_placeholder", config=c, low_liquidity=True)
        self.assertLessEqual(high["next_check_seconds"], low["next_check_seconds"])
