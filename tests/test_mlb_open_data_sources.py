import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.mlb_open_data_sources import (
    REQUIRED_DATA_CATEGORIES,
    build_mlb_open_data_source_report,
    mlb_open_data_sources,
    write_mlb_open_data_source_report,
)


class TestMlbOpenDataSources(unittest.TestCase):
    def test_registry_includes_all_required_categories_and_defaults_disabled(self):
        sources = mlb_open_data_sources()
        categories = {source["data_category"] for source in sources}
        self.assertTrue(set(REQUIRED_DATA_CATEGORIES).issubset(categories))
        self.assertTrue(all(source["module"] == "baseball_mlb" for source in sources))
        self.assertTrue(all(source["enabled"] is False for source in sources))
        self.assertTrue(all(source["provider_write"] is False for source in sources if "provider_write" in source))
        self.assertTrue(all(source["execution_allowed"] is False for source in sources if "execution_allowed" in source))

    def test_source_report_uses_no_spend_safety_flags(self):
        report = build_mlb_open_data_source_report()
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertIn("structured_seed_sources", report)
        self.assertIn("manual_import_sources", report)

    def test_source_report_writes_compact_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_mlb_open_data_source_report(base_data_dir=tmp)
            paths = write_mlb_open_data_source_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            markdown = Path(tmp, paths["latest_markdown_path"])
            rendered = latest.read_text(encoding="utf-8").lower()
            self.assertTrue(latest.exists())
            self.assertTrue(markdown.exists())

        self.assertIn("data_sources/mlb_open_data/sources/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/mlb_open_data/sources/items/", paths["item_json_path"])
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("api_key_value", rendered)


if __name__ == "__main__":
    unittest.main()
