import unittest

from automation_scheduler.no_vig_pricing import (
    calculate_consensus_probability,
    calculate_fair_odds,
    calculate_market_hold,
    remove_three_way_vig,
    remove_two_way_vig,
)


class TestNoVigPricing(unittest.TestCase):
    def test_vig_removal_and_market_hold(self):
        two_way = remove_two_way_vig(0.52381, 0.52381)
        three_way = remove_three_way_vig(0.4, 0.3, 0.35)
        self.assertAlmostEqual(two_way["fair_probability_a"], 0.5, places=3)
        self.assertAlmostEqual(calculate_market_hold([0.4, 0.3, 0.35]), 0.05, places=5)
        self.assertAlmostEqual(sum(three_way[key] for key in ("fair_probability_a", "fair_probability_b", "fair_probability_c")), 1.0, places=5)

    def test_fair_odds_and_consensus_probability(self):
        fair = calculate_fair_odds(0.4)
        self.assertEqual(fair["american_odds"], 150)
        self.assertEqual(calculate_consensus_probability([0.4, 0.42, 0.38]), 0.4)
