import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_open_data_sources import (
    REQUIRED_DATA_CATEGORIES,
    build_nfl_open_data_source_report,
    nfl_open_data_sources,
    write_nfl_open_data_source_report,
)


class TestNflOpenDataSources(unittest.TestCase):
    def test_registry_includes_all_required_categories_and_defaults_disabled(self):
        sources = nfl_open_data_sources()
        categories = {source["data_category"] for source in sources}
        self.assertTrue(set(REQUIRED_DATA_CATEGORIES).issubset(categories))
        self.assertTrue(all(source["module"] == "americanfootball_nfl" for source in sources))
        self.assertTrue(all(source["enabled"] is False for source in sources))
        self.assertTrue(all(source["provider_write"] is False for source in sources))
        self.assertTrue(all(source["execution_allowed"] is False for source in sources))

    def test_no_paid_or_budget_source_is_enabled(self):
        report = build_nfl_open_data_source_report()
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertEqual(report["api_key_required_sources"], [])
        self.assertEqual(report["budget_approval_required_sources"], [])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_budget_approval_is_only_for_future_candidates_if_added(self):
        for source in nfl_open_data_sources():
            if source["requires_budget_approval"]:
                self.assertTrue(source["future_paid_candidate"], json.dumps(source, sort_keys=True))

    def test_source_report_writes_compact_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_open_data_source_report(base_data_dir=tmp)
            paths = write_nfl_open_data_source_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            markdown = Path(tmp, paths["latest_markdown_path"])
            rendered = latest.read_text(encoding="utf-8").lower()
            self.assertTrue(latest.exists())
            self.assertTrue(markdown.exists())

        self.assertIn("data_sources/nfl_open_data/sources/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/nfl_open_data/sources/items/", paths["item_json_path"])
        self.assertNotIn("browser_download_url", rendered)
        self.assertNotIn("api_key_value", rendered)


if __name__ == "__main__":
    unittest.main()
