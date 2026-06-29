import unittest
from src.services.streamlit_dashboard_facade import create_run_context
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestRunContext(unittest.TestCase):
    def test_unique_run_context(self):
        cfg = get_default_scheduler_config()
        a = create_run_context(cfg)
        b = create_run_context(cfg)
        self.assertNotEqual(a["run_id"], b["run_id"])
        self.assertTrue(a["dry_run"])
