import tempfile
import unittest
from pathlib import Path

from automation_scheduler.max_effort_source_discovery import build_architecture_inventory_report, write_architecture_inventory_report


class TestMaxEffortArchitectureInventory(unittest.TestCase):
    def test_report_counts_and_safety_flags(self):
        report = build_architecture_inventory_report()
        summary = report["architecture_summary"]

        self.assertEqual(summary["field_count"], 1770)
        self.assertEqual(summary["source_count"], 59)
        self.assertEqual(summary["partial_field_count"], 194)
        self.assertEqual(summary["blocked_policy_field_count"], 47)
        self.assertEqual(summary["research_field_count"], 32)
        self.assertEqual(summary["model_eligible_field_count"], 295)
        self.assertEqual(report["existing_fields_total"], 1770)
        self.assertEqual(report["existing_fields_completed_count"], 1497)
        self.assertEqual(report["existing_fields_still_empty_count"], 79)
        self.assertEqual(report["paid_source_enabled_count"], 1)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["secrets_included"])

    def test_report_writes_json_and_markdown(self):
        report = build_architecture_inventory_report()
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_architecture_inventory_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())
            self.assertTrue(paths["latest_json_path"].endswith("MAX_EFFORT_ARCHITECTURE_INVENTORY.json"))
            self.assertTrue(paths["latest_markdown_path"].endswith("MAX_EFFORT_ARCHITECTURE_INVENTORY.md"))


if __name__ == "__main__":
    unittest.main()
