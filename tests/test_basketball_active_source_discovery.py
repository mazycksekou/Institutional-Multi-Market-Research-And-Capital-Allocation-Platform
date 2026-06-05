import unittest

from automation_scheduler.basketball_active_source_discovery import run_basketball_active_source_discovery
from automation_scheduler.basketball_free_vs_paid_readiness import SPORTS, build_basketball_active_source_discovery_log


class TestBasketballActiveSourceDiscovery(unittest.TestCase):
    def test_discovery_logs_candidates_for_each_sport(self):
        report = build_basketball_active_source_discovery_log()
        self.assertTrue(report["ok"])
        self.assertEqual({row["sport"] for row in report["source_discovery_log_entries"]}, set(SPORTS))
        self.assertGreater(report["sources_discovered_count"], 0)
        self.assertGreater(report["sources_accepted_count"], 0)
        self.assertGreater(report["sources_rejected_count"], 0)

    def test_runner_preserves_safety_flags(self):
        report = run_basketball_active_source_discovery()
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])


if __name__ == "__main__":
    unittest.main()
