import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_mlb_active_discovery import build_active_source_discovery_log, write_active_source_discovery_log


class TestMlbActiveSourceDiscovery(unittest.TestCase):
    def test_log_contains_accepted_and_rejected_sources(self):
        report = build_active_source_discovery_log(sport="mlb", allow_oxylabs=True, allow_paid_retrieval=True)
        self.assertGreater(report["sources_discovered_count"], 0)
        self.assertGreater(report["sources_accepted_count"], 0)
        self.assertGreater(report["sources_rejected_count"], 0)

    def test_log_writes_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_active_source_discovery_log(sport="mlb", allow_oxylabs=True, allow_paid_retrieval=True)
            paths = write_active_source_discovery_log(report, output_dir=Path(tmp) / "reports", sport="mlb")
        self.assertTrue(paths["latest_json_path"].endswith("reports/MLB_ACTIVE_SOURCE_DISCOVERY_LOG.json"))


if __name__ == "__main__":
    unittest.main()

