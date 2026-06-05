import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.soccer_free_open_exhaustion import build_soccer_final_oxylabs_free_open_exhaustion_report, write_soccer_final_oxylabs_free_open_exhaustion_report


INVENTORY = {"fields_total": 10, "fields_missing_count": 2}
LEDGER = {"summary": {"free_open_populated": 1, "loader_ready_count": 1, "free_open_manual_import_needed": 1, "paid_data_subscription_required": 1, "blocked_reference_or_restricted_source": 1, "policy_blocked": 0, "license_terms_unclear": 0, "unavailable_after_max_effort": 0, "obsolete_or_duplicate": 0}}
SAMPLE = {"sample_results": [{"sample_type": "one_match", "validation_status": "sample_verified"}]}
AUDIT = {
    "source_candidate_count": 4,
    "lanes_tested_count": 4,
    "lanes_with_vague_status": 0,
    "oxylabs_residential_proxy_used": True,
    "oxylabs_web_scraper_api_used": True,
    "oxylabs_total_calls_attempted": 5,
    "oxylabs_total_calls_successful": 5,
    "oxylabs_total_calls_failed": 0,
    "lanes_improved_by_oxylabs": 1,
    "lanes_confirmed_paid_required": 1,
    "lanes_confirmed_manual_import_required": 1,
    "lanes_confirmed_policy_blocked": 1,
    "lanes_confirmed_terms_unclear": 0,
    "lanes_free_open_backfilled": 1,
    "lanes_loader_ready_hard_blocked_from_backfill": 0,
    "lanes_paid_subscription_required": 1,
    "lanes_manual_import_required": 1,
    "lanes_policy_blocked": 1,
    "lanes_license_terms_unclear": 0,
    "lanes_unavailable_after_exhaustive_free_search": 0,
    "lanes_obsolete_or_duplicate": 0,
    "source_candidate_rows": [
        {"source_category": "free_open_populated", "final_actionable_state": "free_open_backfilled", "oxylabs_used": True, "oxylabs_transport_used": "both"},
        {"source_category": "free_open_manual_import_needed", "final_actionable_state": "manual_import_required", "oxylabs_used": True, "oxylabs_transport_used": "web_scraper_api"},
        {"source_category": "paid_data_subscription_required", "final_actionable_state": "paid_subscription_required", "oxylabs_used": True, "oxylabs_transport_used": "web_scraper_api"},
        {"source_category": "blocked_reference_or_restricted_source", "final_actionable_state": "policy_blocked", "oxylabs_used": False, "oxylabs_transport_used": "hard_blocked"},
    ],
}
BACKFILL = {"loader_ready_lanes_before": 1, "loader_ready_lanes_backfilled": 1, "loader_ready_lanes_hard_blocked": 0, "records_added_by_soccer": 10, "fields_closed_this_pass": 10, "fields_partially_closed_this_pass": 0}
RECLASS = {"reclassification_row_count": 2}
SCHEMA = {"new_fields_created_count": 3, "new_tables_created_count": 2}
PAID = {"requirement_rows": [{"lane_name": "tracking_360_context"}]}
READINESS = {"models": [{"recommendation": "manual_import_needed"}]}
CERT = {"free_open_exhaustion_verified": True}


class TestSoccerFinalOxylabsFreeOpenExhaustionReport(unittest.TestCase):
    def test_final_report_declares_exhausted(self):
        fake_lanes = [{"lane_name": "schedule_results"}] * 4
        with patch("automation_scheduler.soccer_free_open_exhaustion.soccer_lane_catalog", return_value=fake_lanes), patch(
            "automation_scheduler.soccer_free_open_exhaustion.build_soccer_source_exhaustion_query_plan",
            return_value={"query_families": ["official_league_team", "public_api_docs", "github_open_source", "csv_parquet_archive", "public_pdf_media_guide", "structured_wiki_supplemental", "dataset_catalog_index", "source_specific_terminology"]},
        ):
            report = build_soccer_final_oxylabs_free_open_exhaustion_report(
                inventory_report=INVENTORY,
                source_ledger=LEDGER,
                sample_report=SAMPLE,
                audit_report=AUDIT,
                backfill_report=BACKFILL,
                reclassification_report=RECLASS,
                schema_expansion_report=SCHEMA,
                paid_matrix=PAID,
                readiness_report=READINESS,
                certificate_report=CERT,
                tests_result="passed",
            )
        self.assertEqual(report["new_overall_verdict"], "SOCCER_FINAL_FREE_OPEN_EXHAUSTED")
        self.assertTrue(report["no_more_free_open_search_required"])
        self.assertEqual(report["lanes_with_vague_status"], 0)

    def test_writer_creates_files(self):
        fake_lanes = [{"lane_name": "schedule_results"}] * 4
        with patch("automation_scheduler.soccer_free_open_exhaustion.soccer_lane_catalog", return_value=fake_lanes), patch(
            "automation_scheduler.soccer_free_open_exhaustion.build_soccer_source_exhaustion_query_plan",
            return_value={"query_families": ["official_league_team", "public_api_docs", "github_open_source", "csv_parquet_archive", "public_pdf_media_guide", "structured_wiki_supplemental", "dataset_catalog_index", "source_specific_terminology"]},
        ):
            report = build_soccer_final_oxylabs_free_open_exhaustion_report(
                inventory_report=INVENTORY,
                source_ledger=LEDGER,
                sample_report=SAMPLE,
                audit_report=AUDIT,
                backfill_report=BACKFILL,
                reclassification_report=RECLASS,
                schema_expansion_report=SCHEMA,
                paid_matrix=PAID,
                readiness_report=READINESS,
                certificate_report=CERT,
                tests_result="passed",
            )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_soccer_final_oxylabs_free_open_exhaustion_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
