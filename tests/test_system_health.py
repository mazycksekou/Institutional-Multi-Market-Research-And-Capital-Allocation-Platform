import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.scheduler_config import get_default_scheduler_config
from automation_scheduler.system_health import get_system_health, write_system_health


class TestSystemHealth(unittest.TestCase):
    def test_health_reports_safe_flags(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            write_system_health(config, {"last_run_id": "abc"})
            health = get_system_health(config)
            self.assertTrue(health["dry_run"])
            self.assertTrue(health["human_approval_required"])
            self.assertFalse(health["auto_execution_enabled"])
            self.assertTrue(all(health["paths_ready"].values()))
            self.assertGreater(health["model_inventory_count"], 0)
            self.assertIn("research_only_count", health)
            self.assertIn("governance_audit_status", health)
