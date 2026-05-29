import unittest
from tempfile import TemporaryDirectory
from automation_scheduler.scheduler_runner import run_scheduler_once


class TestSchedulerRunner(unittest.TestCase):
    def test_dry_run_only(self):
        with TemporaryDirectory() as tmp:
            result = run_scheduler_once(base_data_dir=tmp, dry_run=True, injected_data={"skipped_items": ["a"]})
            self.assertTrue(result["dry_run"])
            self.assertFalse(result["auto_execution_enabled"])
            self.assertIn("report_path", result)
            self.assertIn("records_received", result)
            skipped = [row for row in result.get("skipped_items", []) if isinstance(row, dict)]
            kalshi_skips = [row for row in skipped if row.get("provider_id") == "kalshi_prediction_market"]
            self.assertTrue(kalshi_skips)
