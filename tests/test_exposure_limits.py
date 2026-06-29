import unittest

from src.automation_scheduler_legacy.exposure_limits import apply_all_exposure_caps, cap_daily_exposure, cap_market_group_exposure, cap_single_bet_exposure, cap_weekly_exposure


class ExposureLimitsTests(unittest.TestCase):
    def test_single_bet_cap(self):
        self.assertEqual(cap_single_bet_exposure(7), 5.0)

    def test_daily_cap(self):
        self.assertEqual(cap_daily_exposure(5, 10), 2.0)

    def test_weekly_cap(self):
        self.assertEqual(cap_weekly_exposure(6, 23), 2.0)

    def test_market_group_cap(self):
        self.assertEqual(cap_market_group_exposure(4, 9), 1.0)

    def test_all_caps(self):
        res = apply_all_exposure_caps(6, {"daily_exposure_percent": 3, "weekly_exposure_percent": 10, "market_group_exposure_percent": 2, "correlated_exposure_percent": 1})
        self.assertLessEqual(res["capped_stake_percent"], 5.0)


if __name__ == "__main__":
    unittest.main()
