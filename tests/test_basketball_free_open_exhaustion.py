import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.basketball_free_open_exhaustion import build_basketball_final_gap_plan, write_basketball_final_gap_plan


FAKE_LANES = [
    {
        "sport": "basketball_nba",
        "lane_name": "schedule_results",
        "field_or_feature_group": "schedule results",
        "free_or_paid_category": "free_open_populated",
        "loader_exists": True,
        "final_reason": "free source available",
        "candidate_source_name": "SportsDataverse release assets",
        "source_url_hash": "hash-nba-schedule",
    },
    {
        "sport": "basketball_wnba",
        "lane_name": "lineup_on_off",
        "field_or_feature_group": "lineup on/off",
        "free_or_paid_category": "free_open_partial",
        "loader_exists": True,
        "final_reason": "partial free source available",
        "candidate_source_name": "SportsDataverse release assets",
        "source_url_hash": "hash-wnba-lineup",
    },
]

FAKE_QUERY_PLAN = {
    "lane_query_index": {
        "basketball_nba::schedule_results": [{"query_family": "exact_field_name", "query": "NBA schedule results"}],
        "basketball_wnba::lineup_on_off": [{"query_family": "exact_field_name", "query": "WNBA lineup on/off"}],
    }
}


class TestBasketballFreeOpenExhaustion(unittest.TestCase):
    def test_gap_plan_reports_loader_ready_backfill_progress(self):
        inventory_report = {
            "inventory_entries": [
                {"sport": "basketball_nba", "lane_name": "schedule_results", "field_name": "schedule results", "current_population_status": "partial", "missing_reason": "needs backfill"},
                {"sport": "basketball_wnba", "lane_name": "lineup_on_off", "field_name": "lineup on/off", "current_population_status": "partial", "missing_reason": "needs backfill"},
            ]
        }
        source_ledger = {
            "source_ledger_rows": [
                {
                    "sport": "basketball_nba",
                    "lane_name": "schedule_results",
                    "free_or_paid_category": "free_open_populated",
                    "final_reason": "free source available",
                    "candidate_source_name": "SportsDataverse release assets",
                    "field_or_feature_group": "schedule results",
                },
                {
                    "sport": "basketball_wnba",
                    "lane_name": "lineup_on_off",
                    "free_or_paid_category": "free_open_partial",
                    "final_reason": "partial free source available",
                    "candidate_source_name": "SportsDataverse release assets",
                    "field_or_feature_group": "lineup on/off",
                },
            ]
        }
        sample_report = {"source_result_index": {}}
        audit_report = {
            "source_candidate_rows": [
                {"sport": "basketball_nba", "lane_name": "schedule_results", "oxylabs_used": True, "oxylabs_transport_used": "both", "final_actionable_state": "free_open_backfilled"},
                {"sport": "basketball_wnba", "lane_name": "lineup_on_off", "oxylabs_used": True, "oxylabs_transport_used": "both", "final_actionable_state": "free_open_backfilled"},
            ]
        }
        backfill_report = {"backfill_rows": [{"sport": "basketball_nba", "lane_name": "schedule_results", "backfill_written": True}, {"sport": "basketball_wnba", "lane_name": "lineup_on_off", "backfill_written": True}], "loader_ready_lanes_backfilled": 2, "loader_ready_lanes_hard_blocked": 0}

        with patch("automation_scheduler.basketball_oxylabs_common.basketball_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.basketball_free_open_exhaustion.basketball_lane_catalog",
            return_value=FAKE_LANES,
        ), patch(
            "automation_scheduler.basketball_free_open_exhaustion.build_basketball_source_exhaustion_query_plan",
            return_value=FAKE_QUERY_PLAN,
        ):
            report = build_basketball_final_gap_plan(
                inventory_report=inventory_report,
                source_ledger=source_ledger,
                sample_report=sample_report,
                audit_report=audit_report,
                backfill_report=backfill_report,
            )

        self.assertTrue(report["ok"])
        self.assertEqual(report["gap_row_count"], 4)
        self.assertEqual(report["loader_ready_lanes_backfilled"], 2)
        self.assertEqual(report["loader_ready_lanes_hard_blocked"], 0)
        self.assertGreaterEqual(report["target_state_counts"].get("free_open_backfilled", 0), 2)

    def test_gap_plan_writer_creates_report_files(self):
        report = {
            "gap_rows": [
                {
                    "row_type": "lane",
                    "sport": "basketball_nba",
                    "lane_name": "schedule_results",
                    "field_or_feature_group": "schedule results",
                    "target_final_state": "free_open_backfilled",
                }
            ],
            "gap_row_count": 1,
            "field_gap_row_count": 0,
            "lane_gap_row_count": 1,
            "loader_ready_lanes_backfilled": 2,
            "loader_ready_lanes_hard_blocked": 0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_basketball_final_gap_plan(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
