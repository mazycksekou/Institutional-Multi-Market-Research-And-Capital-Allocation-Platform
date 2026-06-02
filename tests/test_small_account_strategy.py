import unittest

from automation_scheduler.session_risk_rules import evaluate_session_risk, score_time_of_day
from automation_scheduler.small_account_strategy import (
    calculate_risk_reward,
    score_low_float_high_demand,
    score_price_band,
)


class TestSmallAccountStrategy(unittest.TestCase):
    def test_price_band_scoring(self):
        preferred = score_price_band(6)
        self.assertEqual(preferred["price_band"], "preferred_3_to_12")
        self.assertGreater(preferred["small_account_fit_score"], 90)
        below = score_price_band(1.5)
        self.assertEqual(below["price_band"], "below_2_caution")
        self.assertIn("sub_2_dollar_caution", below["no_review_reasons"])

    def test_low_float_high_demand_scoring(self):
        scored = score_low_float_high_demand(
            {
                "price": 7,
                "float_shares": 4_000_000,
                "daily_volume": 16_000_000,
                "relative_volume": 8,
                "intraday_percent_change": 18,
                "catalyst_detected": True,
                "catalyst_type": "fda_update",
                "catalyst_quality_score": 85,
            }
        )
        self.assertEqual(scored["float_rotation"], 4.0)
        self.assertGreaterEqual(scored["low_float_momentum_score"], 70)
        self.assertEqual(scored["low_float_blockers"], [])

    def test_low_float_without_catalyst_is_risk_not_edge(self):
        scored = score_low_float_high_demand(
            {
                "price": 5,
                "float_shares": 3_000_000,
                "daily_volume": 5_000_000,
                "relative_volume": 6,
                "intraday_percent_change": 12,
                "catalyst_detected": False,
            }
        )
        self.assertIn("low_float_without_catalyst_is_risk", scored["low_float_blockers"])

    def test_time_of_day_scoring(self):
        open_drive = score_time_of_day(minutes_since_midnight=9 * 60 + 35)
        midday = score_time_of_day(minutes_since_midnight=12 * 60)
        self.assertEqual(open_drive["session_time_bucket"], "OPENING_DRIVE")
        self.assertGreater(open_drive["time_of_day_edge_score"], midday["time_of_day_edge_score"])

    def test_risk_reward_breakeven_formula(self):
        rr = calculate_risk_reward(10, 9, 12)
        self.assertEqual(rr["reward_risk_ratio"], 2.0)
        self.assertAlmostEqual(rr["breakeven_win_rate"], 1 / 3, places=5)
        poor = calculate_risk_reward(10, 9, 10.5)
        self.assertEqual(poor["risk_reward_permission_status"], "BLOCKED")

    def test_session_walk_away_rules(self):
        locked = evaluate_session_risk({"session_profit": 800, "peak_session_profit": 1000})
        self.assertTrue(locked["session_kill_switch_active"])
        self.assertEqual(locked["session_permission_status"], "NO_TRADE_SESSION_LOCK")
        cooldown = evaluate_session_risk({"consecutive_loss_count": 3})
        self.assertEqual(cooldown["session_permission_status"], "COOLDOWN")
        idle = evaluate_session_risk({"idle_time_without_a_quality_setup_minutes": 61})
        self.assertEqual(idle["session_permission_status"], "REDUCE_PRIORITY")


if __name__ == "__main__":
    unittest.main()
