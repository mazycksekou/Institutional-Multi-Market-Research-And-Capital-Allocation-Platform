import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.scheduler_config import ROI_TARGET_DISCLAIMER, get_default_scheduler_config


class TestSchedulerConfig(unittest.TestCase):
    def test_safe_defaults_and_paths(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            self.assertTrue(config["dry_run"])
            self.assertTrue(config["human_approval_required"])
            self.assertFalse(config["auto_bet_enabled"])
            self.assertFalse(config["auto_trade_enabled"])
            self.assertFalse(config["auto_execution_enabled"])
            self.assertTrue(config["paper_execution_only"])
            self.assertTrue(config["alert_only_mode"])
            for path in config["paths"].values():
                self.assertTrue(path.startswith(tmp))

    def test_competitive_cadence_profiles_exist(self):
        config = get_default_scheduler_config()
        self.assertEqual(config["cadence_profiles"]["sports_pregame_main"]["hot_watchlist_seconds"], 30)
        self.assertEqual(config["cadence_profiles"]["sports_player_props"]["standard_watchlist_seconds"], 90)
        self.assertTrue(config["cadence_profiles"]["sports_live"]["streaming_preferred"])
        self.assertEqual(config["cadence_profiles"]["prediction_markets"]["hot_watchlist_seconds"], 15)
        self.assertEqual(config["cadence_profiles"]["stocks_watchlist"]["broad_scan_seconds"], 60)
        self.assertEqual(config["cadence_profiles"]["stocks_broad"]["slow_scan_seconds"], 300)
        self.assertEqual(config["cadence_profiles"]["news_events"]["broad_scan_seconds"], 900)
        self.assertEqual(config["cadence_profiles"]["low_liquidity"]["standard_scan_seconds"], 300)
        self.assertEqual(ROI_TARGET_DISCLAIMER, "ROI target is a filter target, not a guarantee.")
