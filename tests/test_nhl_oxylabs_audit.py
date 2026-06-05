import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.nhl_oxylabs_audit import build_nhl_oxylabs_source_exhaustion_log, write_nhl_oxylabs_source_exhaustion_log


FAKE_LANES = [
    {
        "sport": "icehockey_nhl",
        "lane_name": "schedule_results",
        "field_or_feature_group": "schedule/results",
        "candidate_source_name": "NHL public API",
        "source_url_hash": "hash-schedule",
        "free_or_paid_category": "free_open_populated",
        "loader_exists": True,
        "fields": ["game_id"],
    },
    {
        "sport": "icehockey_nhl",
        "lane_name": "injuries_availability",
        "field_or_feature_group": "injuries",
        "candidate_source_name": "NHL team roster page",
        "source_url_hash": "hash-injuries",
        "free_or_paid_category": "free_open_manual_import_needed",
        "loader_exists": False,
        "fields": ["injury_status"],
    },
    {
        "sport": "icehockey_nhl",
        "lane_name": "goalie_gsaax_dataset",
        "field_or_feature_group": "goalie gsaax",
        "candidate_source_name": "Paid vendor page",
        "source_url_hash": "hash-gsaax",
        "free_or_paid_category": "paid_data_subscription_required",
        "loader_exists": False,
        "fields": ["goalie_recent_goals_saved_above_expected_proxy"],
    },
    {
        "sport": "icehockey_nhl",
        "lane_name": "restricted_reference_tables",
        "field_or_feature_group": "reference tables",
        "candidate_source_name": "Hockey Reference",
        "source_url_hash": "hash-reference",
        "free_or_paid_category": "blocked_reference_or_restricted_source",
        "loader_exists": False,
        "fields": ["reference_duplicate_box_score"],
    },
]


FAKE_QUERY_INDEX = {f"{lane['sport']}::{lane['lane_name']}": [{"query": f"{lane['lane_name']} query"}] for lane in FAKE_LANES}


def _fake_loader_result(*args, **kwargs):
    return {
        "ok": True,
        "normalized_records": [{"game_id": 1}],
        "normalized_record_count": 1,
        "oxylabs_used": True,
        "oxylabs_transport_used": "residential_proxy",
        "oxylabs_calls_attempted": 1,
        "oxylabs_calls_successful": 1,
        "oxylabs_calls_failed": 0,
        "source_name": "NHL public API",
    }


class TestNhlOxylabsAudit(unittest.TestCase):
    def test_audit_classifies_final_states(self):
        with patch("automation_scheduler.nhl_oxylabs_audit.nhl_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.nhl_oxylabs_audit.build_nhl_source_exhaustion_query_plan",
            return_value={"lane_query_index": FAKE_QUERY_INDEX},
        ), patch("automation_scheduler.nhl_oxylabs_audit._official_page_confirmation", return_value={"ok": True}), patch(
            "automation_scheduler.nhl_oxylabs_audit.load_nhl_lane_records",
            side_effect=_fake_loader_result,
        ), patch(
            "automation_scheduler.nhl_oxylabs_audit.fetch_public_page_text",
            return_value={"ok": True, "status": "ok"},
        ):
            report = build_nhl_oxylabs_source_exhaustion_log()
        self.assertTrue(report["ok"])
        self.assertEqual(report["lanes_tested_count"], len(FAKE_LANES))
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])
        self.assertEqual(report["lanes_with_vague_status"], 0)

    def test_writer_creates_files(self):
        report = {
            "ok": True,
            "source_candidate_count": 1,
            "lanes_tested_count": 1,
            "oxylabs_total_calls_attempted": 1,
            "oxylabs_total_calls_successful": 1,
            "oxylabs_total_calls_failed": 0,
            "source_candidate_rows": [{"lane_name": "schedule_results", "final_actionable_state": "free_open_backfilled", "oxylabs_transport_used": "both", "normalized_records_added": 1}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_oxylabs_source_exhaustion_log(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
