import unittest

from src.services.streamlit_dashboard_facade import simulate_middle_ev


class TestMiddleEvSimulator(unittest.TestCase):
    def test_middle_ev_positive_or_negative(self):
        positive = simulate_middle_ev(left_odds_american=-110, right_odds_american=-110, middle_hit_probability=0.25)
        negative = simulate_middle_ev(left_odds_american=-130, right_odds_american=-130, middle_hit_probability=0.01)
        self.assertGreater(positive["estimated_ev"], 0)
        self.assertLess(negative["estimated_ev"], 0)
