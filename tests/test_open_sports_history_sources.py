import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.open_sports_history_sources import (
    build_open_sports_history_source_report,
    open_sports_history_sources,
    write_open_sports_history_source_report,
)


class TestOpenSportsHistorySources(unittest.TestCase):
    def _sources_by_id(self):
        return {source["source_id"]: source for source in open_sports_history_sources()}

    def test_source_registry_writes_compact_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_open_sports_history_source_report(base_data_dir=tmp)
            paths = write_open_sports_history_source_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            latest_md = Path(tmp, paths["latest_markdown_path"])
            rendered = latest.read_text(encoding="utf-8").lower()
            self.assertTrue(latest.exists())
            self.assertTrue(latest_md.exists())

        self.assertIn("data_sources/open_sports_history/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/open_sports_history/items/", paths["item_json_path"])
        self.assertIn("data_sources/open_sports_history/daily/", paths["daily_markdown_path"])
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("api_key_value", rendered)

    def test_retrosheet_and_nflverse_are_approved_but_disabled(self):
        sources = self._sources_by_id()
        for source_id in ("retrosheet_mlb", "nflverse_nfl"):
            source = sources[source_id]
            self.assertEqual(source["approval_status"], "approved_open_historical")
            self.assertTrue(source["current_phase_allowed"])
            self.assertTrue(source["supports_direct_download"])
            self.assertTrue(source["supports_local_file_import"])
            self.assertFalse(source["enabled"])
            self.assertFalse(source["provider_write"])
            self.assertFalse(source["execution_allowed"])

    def test_sportsdataverse_sources_are_verification_lanes_and_disabled(self):
        sources = self._sources_by_id()
        for source_id in (
            "sportsdataverse_ncaaf",
            "sportsdataverse_ncaab",
            "sportsdataverse_ncaaw",
            "sportsdataverse_wnba",
        ):
            source = sources[source_id]
            self.assertEqual(source["approval_status"], "needs_tiny_verification")
            self.assertTrue(source["current_phase_allowed"])
            self.assertFalse(source["supports_direct_download"])
            self.assertFalse(source["enabled"])
            self.assertTrue(source["terms_review_required"])

    def test_sports_reference_is_manual_export_terms_review_only(self):
        source = self._sources_by_id()["sports_reference_manual_export"]
        self.assertEqual(source["source_kind"], "manual_export")
        self.assertEqual(source["source_access_type"], "manual_export_terms_review")
        self.assertEqual(source["approval_status"], "terms_review_required")
        self.assertEqual(source["blocked_reason"], "manual_export_only_no_scraping")
        self.assertTrue(source["supports_manual_export"])
        self.assertFalse(source["supports_direct_download"])
        self.assertFalse(source["current_phase_allowed"])
        self.assertFalse(source["enabled"])

    def test_enabled_and_paid_source_counts_remain_zero(self):
        report = build_open_sports_history_source_report()
        self.assertEqual(report["sources_registered"], 7)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_all_required_registry_fields_are_present(self):
        required = {
            "source_id",
            "module",
            "source_name",
            "source_kind",
            "source_access_type",
            "current_phase_allowed",
            "future_paid_candidate",
            "requires_budget_approval",
            "approval_status",
            "enabled",
            "supports_direct_download",
            "supports_local_file_import",
            "supports_manual_export",
            "supports_api_key",
            "terms_review_required",
            "recommended_use",
            "blocked_reason",
            "max_records_default",
            "max_records_hard_cap",
            "raw_payload_persistence_allowed",
            "provider_write",
            "execution_allowed",
        }
        for source in open_sports_history_sources():
            self.assertTrue(required.issubset(source), json.dumps(source, sort_keys=True))
            self.assertFalse(source["raw_payload_persistence_allowed"])


if __name__ == "__main__":
    unittest.main()
