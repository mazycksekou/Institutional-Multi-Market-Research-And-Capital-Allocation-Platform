import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.soccer_oxylabs_audit import build_soccer_oxylabs_source_exhaustion_log, write_soccer_oxylabs_source_exhaustion_log


FAKE_LANES = [
    {"sport": "soccer", "lane_name": "schedule_results", "field_or_feature_group": "fixtures", "candidate_source_name": "football-data.co.uk", "source_url_hash": "hash-1", "free_or_paid_category": "free_open_populated", "loader_exists": True, "fields": ["stable_match_key"], "source_id": "soccer_football_data_csv"},
    {"sport": "soccer", "lane_name": "injuries_availability", "field_or_feature_group": "injuries", "candidate_source_name": "Official page", "source_url_hash": "hash-2", "free_or_paid_category": "free_open_manual_import_needed", "loader_exists": False, "fields": ["availability_status"], "source_id": "soccer_official_league_page"},
    {"sport": "soccer", "lane_name": "tracking_360_context", "field_or_feature_group": "tracking", "candidate_source_name": "StatsBomb 360", "source_url_hash": "hash-3", "free_or_paid_category": "paid_data_subscription_required", "loader_exists": False, "fields": ["tracking_available"], "source_id": "soccer_statsbomb_paid_vendor_page"},
    {"sport": "soccer", "lane_name": "restricted_reference_tables", "field_or_feature_group": "reference", "candidate_source_name": "FBref", "source_url_hash": "hash-4", "free_or_paid_category": "blocked_reference_or_restricted_source", "loader_exists": False, "fields": ["restricted_duplicate_stats"], "source_id": "soccer_fbref_blocked"},
]

FAKE_QUERY_INDEX = {f"{lane['sport']}::{lane['lane_name']}": [{"query": f"{lane['lane_name']} query"}] for lane in FAKE_LANES}


class TestSoccerOxylabsAudit(unittest.TestCase):
    def test_audit_classifies_final_states(self):
        with patch("automation_scheduler.soccer_oxylabs_audit.soccer_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.soccer_oxylabs_audit.build_soccer_source_exhaustion_query_plan",
            return_value={"lane_query_index": FAKE_QUERY_INDEX},
        ), patch(
            "automation_scheduler.soccer_oxylabs_audit.load_soccer_lane_records",
            return_value={"ok": True, "normalized_records": [{"stable_match_key": "x"}], "normalized_record_count": 1, "oxylabs_used": True, "oxylabs_transport_used": "residential_proxy", "oxylabs_calls_attempted": 1, "oxylabs_calls_successful": 1, "oxylabs_calls_failed": 0, "source_name": "football-data.co.uk"},
        ), patch(
            "automation_scheduler.soccer_oxylabs_audit.fetch_public_page_text",
            return_value={"ok": True, "status": "ok"},
        ):
            report = build_soccer_oxylabs_source_exhaustion_log()
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])
        self.assertEqual(report["lanes_with_vague_status"], 0)

    def test_writer_creates_files(self):
        report = {"source_candidate_count": 1, "lanes_tested_count": 1, "oxylabs_total_calls_attempted": 1, "oxylabs_total_calls_successful": 1, "oxylabs_total_calls_failed": 0, "source_candidate_rows": [{"lane_name": "schedule_results", "final_actionable_state": "free_open_backfilled", "oxylabs_transport_used": "both", "normalized_records_added": 1}]}
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_soccer_oxylabs_source_exhaustion_log(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
