import unittest
from tempfile import TemporaryDirectory
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestSchedulerConfig(unittest.TestCase):
    def test_safe_defaults(self):
        with TemporaryDirectory() as tmp:
            c = get_default_scheduler_config(base_data_dir=tmp)
            self.assertTrue(c["dry_run"])
            self.assertTrue(c["human_approval_required"])
            self.assertFalse(c["auto_bet_enabled"])
            self.assertFalse(c["auto_trade_enabled"])
            self.assertFalse(c["auto_execution_enabled"])
            self.assertTrue(c["paper_execution_only"])
            self.assertTrue(c["roi_target_is_filter_only"])

    def test_market_cadences_exist(self):
        c = get_default_scheduler_config()
        self.assertEqual(c["cadence_profiles"]["sports_pregame_main"]["hot_watchlist_seconds"], 60)
        self.assertEqual(c["cadence_profiles"]["sports_player_props"]["hot_watchlist_seconds"], 90)
        self.assertEqual(c["cadence_profiles"]["sports_live"]["hot_watchlist_seconds"], 15)
