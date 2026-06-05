import tempfile
import unittest
from pathlib import Path

from automation_scheduler.basketball_free_open_exhaustion import (
    build_basketball_final_oxylabs_free_open_exhaustion_report,
    write_basketball_final_oxylabs_free_open_exhaustion_report,
)


AUDIT_REPORT = {
    "lanes_with_vague_status": 0,
    "oxylabs_residential_proxy_used": True,
    "oxylabs_web_scraper_api_used": True,
    "oxylabs_total_calls_attempted": 5,
    "oxylabs_total_calls_successful": 5,
    "oxylabs_total_calls_failed": 0,
    "lanes_improved_by_oxylabs": 2,
    "lanes_confirmed_paid_required": 1,
    "lanes_confirmed_manual_import_required": 1,
    "lanes_confirmed_policy_blocked": 1,
    "lanes_confirmed_terms_unclear": 0,
    "lanes_free_open_backfilled": 2,
    "lanes_loader_ready_hard_blocked_from_backfill": 0,
    "lanes_paid_subscription_required": 1,
    "lanes_manual_import_required": 1,
    "lanes_policy_blocked": 1,
    "lanes_license_terms_unclear": 0,
    "lanes_unavailable_after_exhaustive_free_search": 0,
    "lanes_obsolete_or_duplicate": 0,
    "source_candidate_rows": [
        {"sport": "basketball_nba", "lane_name": "schedule_results", "accepted_or_rejected": "accepted", "final_actionable_state": "free_open_backfilled", "source_category": "free_open_populated", "normalized_records_found": 2, "normalized_records_added": 2, "source_name": "SportsDataverse release assets", "source_url_hash": "hash-nba", "domain": "github.com", "source_type": "open_release_asset", "query_used": "NBA schedule results", "rejection_reason": "", "license_or_terms_note": ""},
        {"sport": "basketball_wnba", "lane_name": "lineup_on_off", "accepted_or_rejected": "accepted", "final_actionable_state": "free_open_backfilled", "source_category": "free_open_partial", "normalized_records_found": 2, "normalized_records_added": 2, "source_name": "SportsDataverse release assets", "source_url_hash": "hash-wnba", "domain": "github.com", "source_type": "open_release_asset", "query_used": "WNBA lineup on/off", "rejection_reason": "", "license_or_terms_note": ""},
    ],
}

BACKFILL_REPORT = {
    "loader_ready_lanes_backfilled": 2,
    "loader_ready_lanes_hard_blocked": 0,
    "fields_closed_this_pass": 7,
    "fields_partially_closed_this_pass": 0,
    "fields_reclassified_this_pass": 1,
    "records_added_by_sport": {
        "basketball_nba": 2,
        "basketball_wnba": 2,
        "basketball_ncaab": 0,
        "basketball_ncaaw": 0,
    },
    "oxylabs_residential_proxy_used": True,
    "oxylabs_total_calls_attempted": 2,
    "oxylabs_total_calls_successful": 2,
    "oxylabs_total_calls_failed": 0,
}

SOURCE_LEDGER = {
    "source_ledger_rows": [
        {"sport": "basketball_nba", "lane_name": "schedule_results", "free_or_paid_category": "free_open_populated"},
        {"sport": "basketball_wnba", "lane_name": "lineup_on_off", "free_or_paid_category": "free_open_partial"},
        {"sport": "basketball_ncaab", "lane_name": "strength_of_schedule_context", "free_or_paid_category": "free_open_manual_import_needed"},
        {"sport": "basketball_ncaaw", "lane_name": "injuries_availability", "free_or_paid_category": "paid_data_subscription_required"},
    ],
    "summary": {
        "source_count": 4,
        "free_open_populated": 1,
        "free_open_partial": 1,
        "free_open_manual_import_needed": 1,
        "paid_data_subscription_required": 1,
        "policy_blocked": 0,
        "blocked_reference_or_restricted_source": 0,
        "license_terms_unclear": 0,
        "unavailable_after_max_effort": 0,
        "obsolete_or_duplicate": 0,
    },
}

SAMPLE_RESULTS = {
    "sample_verified_count": 2,
    "sample_blocked_count": 0,
    "sample_no_records_count": 0,
    "by_sport": {
        "basketball_nba": {"records_tested": 1},
        "basketball_wnba": {"records_tested": 1},
        "basketball_ncaab": {"records_tested": 0},
        "basketball_ncaaw": {"records_tested": 0},
    },
}

INVENTORY = {
    "fields_total": 389,
    "fields_populated_count": 299,
    "fields_partial_count": 0,
    "fields_missing_count": 90,
}

SCHEMA_EXPANSION = {
    "new_fields_created_count": 53,
    "new_tables_created_count": 8,
    "new_fields_created": [],
    "new_tables_created": [],
}

PAID_MATRIX = {"requirement_rows": [{"lane_name": "injuries_availability"}], "paid_required_count": 1}

READINESS = {
    "models": [
        {"sport": "basketball_nba", "recommendation": "ready_but_paid_data_would_improve"},
        {"sport": "basketball_wnba", "recommendation": "ready_but_paid_data_would_improve"},
        {"sport": "basketball_ncaab", "recommendation": "manual_import_needed"},
        {"sport": "basketball_ncaaw", "recommendation": "manual_import_needed"},
    ]
}

CERTIFICATE = {"free_open_exhaustion_verified": True, "free_open_sources_checked_count": 5}


class TestBasketballFinalOxylabsFreeOpenExhaustionReport(unittest.TestCase):
    def test_final_report_declares_free_open_exhausted(self):
        report = build_basketball_final_oxylabs_free_open_exhaustion_report(
            audit_report=AUDIT_REPORT,
            backfill_report=BACKFILL_REPORT,
            gap_plan={"ok": True},
            readiness=READINESS,
            paid_matrix=PAID_MATRIX,
            certificate=CERTIFICATE,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["new_overall_verdict"], "BASKETBALL_FINAL_FREE_OPEN_EXHAUSTED")
        self.assertEqual(report["loader_ready_lanes_backfilled"], 2)
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])

    def test_writer_creates_report_files(self):
        report = build_basketball_final_oxylabs_free_open_exhaustion_report(
            audit_report=AUDIT_REPORT,
            backfill_report=BACKFILL_REPORT,
            gap_plan={"ok": True},
            readiness=READINESS,
            paid_matrix=PAID_MATRIX,
            certificate=CERTIFICATE,
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_basketball_final_oxylabs_free_open_exhaustion_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
