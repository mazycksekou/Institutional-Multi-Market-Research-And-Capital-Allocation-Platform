import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nfl_open_data_source_exhaustion import (
    CANDIDATE_SOURCE_FAMILIES,
    build_nfl_source_exhaustion_report,
    classify_candidate_source,
    nfl_candidate_sources,
    write_nfl_source_exhaustion_report,
)
from automation_scheduler.nfl_open_data_field_catalog import (
    build_existing_nfl_field_index,
    build_source_field_diff_report,
    classify_candidate_field_novelty,
)


class TestNflSourceExhaustion(unittest.TestCase):
    def test_registry_scans_candidate_families(self):
        report = build_nfl_source_exhaustion_report()
        families = {c["source_family"] for c in report["candidates"]}
        self.assertTrue(families.issubset(set(CANDIDATE_SOURCE_FAMILIES)))
        self.assertGreaterEqual(report["candidate_sources_found"], 8)
        self.assertTrue(report["nfl_source_exhaustion_checked"])

    def test_redundant_sources_are_skipped(self):
        report = build_nfl_source_exhaustion_report()
        self.assertIn("nflverse_nflfastr_pbp_release", report["nfl_redundant_sources_skipped"])
        self.assertIn("sportsdataverse_nfl_open", report["nfl_redundant_sources_skipped"])

    def test_paid_or_auth_sources_blocked(self):
        classified = classify_candidate_source({"paid_or_freemium": True, "automation_allowed": True, "structured_data_available": True, "terms_review_status": "reviewed_open_allowed"})
        self.assertEqual(classified["blocker"], "paid_or_budget_required")
        auth = classify_candidate_source({"requires_api_key": True, "automation_allowed": True, "structured_data_available": True, "terms_review_status": "reviewed_open_allowed"})
        self.assertEqual(auth["blocker"], "auth_or_api_key_required")

    def test_spoofing_source_blocked(self):
        classified = classify_candidate_source({"spoofing_required": True})
        self.assertEqual(classified["blocker"], "spoofing_or_bypass_required")
        self.assertFalse(classified["current_phase_allowed"])

    def test_raw_html_unclear_terms_blocked(self):
        classified = classify_candidate_source(
            {"raw_html_required": True, "terms_review_status": "terms_unclear", "automation_allowed": True, "structured_data_available": True}
        )
        self.assertEqual(classified["blocker"], "html_scraping_terms_unclear")

    def test_pfr_remains_blocked(self):
        sources = {c["source_id"]: c for c in nfl_candidate_sources()}
        self.assertEqual(sources["pro_football_reference_web"]["blocker"], "sports_reference_scraping_blocked")
        self.assertFalse(sources["pro_football_reference_web"]["current_phase_allowed"])

    def test_ftn_remains_blocked(self):
        sources = {c["source_id"]: c for c in nfl_candidate_sources()}
        self.assertEqual(sources["ftn_charting_open_candidate"]["approval_status"], "blocked")

    def test_no_spoofing_or_browser_impersonation(self):
        report = build_nfl_source_exhaustion_report()
        self.assertFalse(report["spoofing_used"])
        self.assertFalse(report["browser_impersonation_used"])
        self.assertFalse(report["raw_html_persisted"])
        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["downloads_attempted"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)

    def test_field_diff_marks_new_and_duplicate_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            sched = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / "nflverse_schedules_results" / "latest.json"
            sched.parent.mkdir(parents=True, exist_ok=True)
            sched.write_text('{"fields_available": ["game_id", "home_score"], "field_types": {}, "seasons_available": ["2024"]}', encoding="utf-8")
            index = build_existing_nfl_field_index(base_data_dir=tmp)
            dup = classify_candidate_field_novelty({"field_name": "game_id"}, index)
            new = classify_candidate_field_novelty({"field_name": "head_coach"}, index)
        self.assertTrue(dup["exact_duplicate"])
        self.assertFalse(dup["ingestible"])
        self.assertTrue(new["new_field"])
        self.assertTrue(new["ingestible"])

    def test_source_field_diff_report_skips_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            sched = Path(tmp) / "data_sources" / "nfl_open_data" / "validated" / "nflverse_schedules_results" / "latest.json"
            sched.parent.mkdir(parents=True, exist_ok=True)
            sched.write_text('{"fields_available": ["game_id"], "field_types": {}, "seasons_available": ["2024"]}', encoding="utf-8")
            report = build_source_field_diff_report(
                source_id="candidate_x",
                candidate_fields=[{"field_name": "game_id"}, {"field_name": "head_coach"}],
                base_data_dir=tmp,
            )
        self.assertIn("head_coach", report["ingestible_fields"])
        self.assertIn("game_id", report["duplicate_fields"])

    def test_report_writes_without_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_nfl_source_exhaustion_report(base_data_dir=tmp)
            paths = write_nfl_source_exhaustion_report(report, base_data_dir=tmp)
            latest = Path(tmp, paths["latest_json_path"])
            latest_exists = latest.exists()
            rendered = latest.read_text(encoding="utf-8").lower()
        self.assertTrue(latest_exists)
        self.assertIn("data_sources/nfl_open_data/source_exhaustion/latest.json", paths["latest_json_path"])
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("provider_payload", rendered)


if __name__ == "__main__":
    unittest.main()
