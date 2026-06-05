import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_mlb_active_discovery import build_field_inventory_report, write_field_inventory_report


class TestFieldInventoryCompletion(unittest.TestCase):
    def test_inventory_classifies_every_field(self):
        report = build_field_inventory_report()
        self.assertGreater(report["existing_fields_total"], 0)
        self.assertEqual(report["existing_fields_total"], len(report["field_inventory_entries"]))
        allowed = {"populated", "partial", "empty", "stale", "blocked_policy", "blocked_paid_required", "research", "unknown"}
        self.assertTrue(all(row["current_population_status"] in allowed for row in report["field_inventory_entries"]))
        self.assertGreater(report["source_queries_run_count"], 0)

    def test_inventory_writes_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_field_inventory_report()
            paths = write_field_inventory_report(report, output_dir=Path(tmp) / "reports")
        self.assertTrue(paths["latest_json_path"].endswith("reports/NFL_MLB_FIELD_INVENTORY_BEFORE_EXPANSION.json"))
        self.assertTrue(paths["latest_markdown_path"].endswith("reports/NFL_MLB_FIELD_INVENTORY_BEFORE_EXPANSION.md"))


if __name__ == "__main__":
    unittest.main()

