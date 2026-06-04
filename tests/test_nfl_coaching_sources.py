import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_coaching_sources import (
    COACHING_SOURCE_FAMILIES,
    COACHING_TARGET_FIELDS,
    MIN_CRAWL_DELAY_SECONDS,
    RESEARCH_USER_AGENT,
    build_nfl_coaching_source_report,
    classify_coaching_source,
    coaching_source_by_id,
    nfl_coaching_sources,
    write_nfl_coaching_source_report,
)


class TestNflCoachingSources(unittest.TestCase):
    def _families(self):
        return {s["source_family"] for s in nfl_coaching_sources()}

    def test_registry_includes_official_staff_pages(self):
        self.assertIn("official_team_staff_pages", self._families())

    def test_registry_includes_official_press_releases(self):
        self.assertIn("official_team_press_releases", self._families())

    def test_registry_includes_wikidata_seed(self):
        self.assertIn("wikidata_coaching_seed", self._families())

    def test_registry_includes_wikipedia_seed(self):
        self.assertIn("wikipedia_coaching_seed", self._families())

    def test_registry_includes_manual_csv_import(self):
        self.assertIn("manual_csv_import", self._families())

    def test_registry_covers_all_declared_families(self):
        self.assertEqual(self._families(), set(COACHING_SOURCE_FAMILIES))

    def test_all_sources_disabled_by_default(self):
        for source in nfl_coaching_sources():
            self.assertFalse(source["enabled"])
            self.assertEqual(source["user_agent"], RESEARCH_USER_AGENT)
            self.assertFalse(source["spoofing_required"])
            self.assertFalse(source["browser_impersonation_used"])
            self.assertFalse(source["raw_html_persisted"])
            self.assertGreaterEqual(source["crawl_delay_seconds"], MIN_CRAWL_DELAY_SECONDS)
            self.assertEqual(source["data_category"], "coaching_staff")

    def test_wikidata_and_wikipedia_are_structured_approved(self):
        sources = {s["source_id"]: s for s in nfl_coaching_sources()}
        self.assertEqual(sources["wikidata_coaching_seed"]["approval_status"], "approved_open_structured")
        self.assertEqual(sources["wikipedia_coaching_seed"]["approval_status"], "approved_open_structured")
        self.assertEqual(sources["manual_csv_import"]["approval_status"], "approved_manual_import")

    def test_pfr_and_ftn_blocked(self):
        sources = {s["source_id"]: s for s in nfl_coaching_sources()}
        self.assertEqual(sources["blocked_pfr_reference"]["blocker"], "sports_reference_scraping_blocked")
        self.assertEqual(sources["blocked_ftn_charting"]["approval_status"], "blocked")

    def test_robots_disallow_blocks_html_source(self):
        classified = classify_coaching_source(
            {"source_kind": "html_pages", "robots_review_status": "disallows_automated_collection", "raw_html_required": True, "terms_review_status": "terms_unclear", "automation_allowed": True, "structured_data_available": False}
        )
        self.assertEqual(classified["blocker"], "robots_disallows_automation")

    def test_unverified_license_blocks_open_file(self):
        classified = classify_coaching_source(
            {"source_kind": "open_data_file", "license_status": "license_unverified", "automation_allowed": True, "structured_data_available": True, "terms_review_status": "research_required"}
        )
        self.assertEqual(classified["blocker"], "license_unverified")

    def test_report_blocked_until_rows_ingested(self):
        report = build_nfl_coaching_source_report()
        self.assertFalse(report["nfl_coaching_data_available"])
        self.assertEqual(report["nfl_coaching_data_blocked_reason"], "no_coaching_rows_ingested_yet_sources_disabled_by_default")
        self.assertEqual(report["coaching_target_fields"], COACHING_TARGET_FIELDS)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)

    def test_report_writes_without_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_coaching_source_report(base_data_dir=tmp)
            paths = write_nfl_coaching_source_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            latest_exists = latest.exists()
            rendered = latest.read_text(encoding="utf-8").lower()
        self.assertTrue(latest_exists)
        self.assertIn("data_sources/nfl_open_data/coaching_sources/latest.json", paths["latest_json_path"])
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("provider_payload", rendered)
        self.assertIsNotNone(coaching_source_by_id("manual_csv_import"))


if __name__ == "__main__":
    unittest.main()
