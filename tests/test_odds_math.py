import unittest

from automation_scheduler.odds_math import (
    american_to_decimal,
    american_to_implied_probability,
    calculate_ev,
    calculate_payout,
    calculate_profit_loss,
    calculate_roi,
    decimal_to_american,
    remove_two_way_vig,
)


class TestOddsMath(unittest.TestCase):
    def test_odds_conversions_work(self):
        self.assertAlmostEqual(american_to_decimal(-110), 1.909091, places=5)
        self.assertAlmostEqual(american_to_decimal(150), 2.5, places=5)
        self.assertAlmostEqual(american_to_implied_probability(-110), 0.52381, places=5)
        self.assertEqual(decimal_to_american(2.5), 150)

    def test_vig_ev_roi_and_payout_math_work(self):
        fair = remove_two_way_vig(0.52381, 0.52381)
        self.assertAlmostEqual(fair["fair_probability_a"], 0.5, places=3)
        payout = calculate_payout(100, 150)
        profit = calculate_profit_loss(100, 150, won=True)
        ev = calculate_ev(100, 0.5, 150)
        roi = calculate_roi(100, ev)
        self.assertEqual(payout, 250.0)
        self.assertEqual(profit, 150.0)
        self.assertEqual(ev, 25.0)
        self.assertEqual(roi, 25.0)
