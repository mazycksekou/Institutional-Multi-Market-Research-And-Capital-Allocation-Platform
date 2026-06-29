import unittest
from tempfile import TemporaryDirectory
from src.services.streamlit_dashboard_facade import get_default_scheduler_config
from src.services.streamlit_dashboard_facade import get_system_health


class TestSystemHealth(unittest.TestCase):
    def test_safe_json(self):
        with TemporaryDirectory() as tmp:
            c = get_default_scheduler_config(base_data_dir=tmp)
            h = get_system_health(c)
            self.assertTrue(h["dry_run"])
            self.assertTrue(h["human_approval_required"])
            self.assertFalse(h["auto_execution_enabled"])
            self.assertIn("enabled_provider_count", h)
            self.assertIn("live_calls_enabled_count", h)
