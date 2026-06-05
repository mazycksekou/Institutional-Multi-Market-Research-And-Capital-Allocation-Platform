import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.basketball_oxylabs_audit import (
    build_basketball_oxylabs_source_exhaustion_log,
    write_basketball_oxylabs_source_exhaustion_log,
)


FAKE_LANES = [
    {
        "sport": "basketball_nba",
        "lane_name": "schedule_results",
        "field_or_feature_group": "schedule results",
        "candidate_source_name": "SportsDataverse release assets",
        "source_url_hash": "hash-nba-schedule",
        "free_or_paid_category": "free_open_populated",
        "loader_exists": True,
        "sample": {"release_tag": "espn_nba_schedules", "asset_name": "nba_schedule_2025.csv"},
    },
    {
        "sport": "basketball_wnba",
        "lane_name": "lineup_on_off",
        "field_or_feature_group": "lineup on/off",
        "candidate_source_name": "SportsDataverse release assets",
        "source_url_hash": "hash-wnba-lineup",
        "free_or_paid_category": "free_open_partial",
        "loader_exists": True,
        "sample": {"release_tag": "wnba_lineups", "asset_name": "wnba_lineups_2025.csv"},
    },
    {
        "sport": "basketball_ncaab",
        "lane_name": "strength_of_schedule_context",
        "field_or_feature_group": "strength of schedule context",
        "candidate_source_name": "NCAA NET rankings page",
        "source_url_hash": "hash-ncaab-net",
        "free_or_paid_category": "free_open_manual_import_needed",
        "loader_exists": False,
        "sample": {"release_tag": "ncaab_net", "asset_name": "ncaab_net.csv"},
    },
    {
        "sport": "basketball_ncaaw",
        "lane_name": "injuries_availability",
        "field_or_feature_group": "injuries availability",
        "candidate_source_name": "Sportradar basketball docs",
        "source_url_hash": "hash-ncaaw-injuries",
        "free_or_paid_category": "paid_data_subscription_required",
        "loader_exists": False,
        "sample": {"release_tag": "ncaaw_injuries", "asset_name": "ncaaw_injuries.csv"},
    },
    {
        "sport": "basketball_nba",
        "lane_name": "restricted_reference_tables",
        "field_or_feature_group": "restricted reference tables",
        "candidate_source_name": "Basketball Reference",
        "source_url_hash": "hash-nba-reference",
        "free_or_paid_category": "policy_blocked",
        "loader_exists": False,
        "sample": {"release_tag": "blocked", "asset_name": "blocked.csv"},
    },
]

FAKE_QUERY_INDEX = {
    f"{lane['sport']}::{lane['lane_name']}": [{"query": f"{lane['lane_name']} query"}]
    for lane in FAKE_LANES
}

FAKE_RELEASE_ROWS = [
    {
        "game_id": "g1",
        "season": "2025",
        "game_date": "2025-01-01",
        "season_type": "2",
        "team_id": "1",
        "team_display_name": "Team A",
        "team_abbreviation": "A",
        "team_score": "100",
        "assists": "20",
        "field_goals_attempted": "80",
        "free_throws_attempted": "18",
        "offensive_rebounds": "9",
        "turnovers": "12",
        "total_rebounds": "44",
        "gp": "10",
        "group_set": "set-a",
        "group_id": "gid-a",
        "group_name": "Lineup A",
        "w": "7",
        "l": "3",
        "w_pct": "0.7",
        "min": "250",
        "pts": "110",
        "plus_minus": "8",
        "athlete_id": "101",
        "athlete_display_name": "Player One",
        "minutes": "32:10",
        "rebounds": "8",
        "points": "18",
        "starter": "true",
        "active": "true",
        "did_not_play": "false",
        "official_full_name": "Ref One",
        "official_display_name": "Ref One",
        "official_position": "Crew Chief",
        "official_position_id": "1",
        "official_order": "1",
        "type_id": "1",
        "type_text": "shot",
        "text": "Made shot",
        "clock_display_value": "12:00",
        "score_value": "2",
        "scoring_play": "true",
        "period_number": "1",
        "period_display_value": "Q1",
        "coordinate_x": "10",
        "coordinate_y": "5",
        "coordinate_x_raw": "10",
        "coordinate_y_raw": "5",
    },
    {
        "game_id": "g2",
        "season": "2025",
        "game_date": "2025-01-02",
        "season_type": "2",
        "team_id": "2",
        "team_display_name": "Team B",
        "team_abbreviation": "B",
        "team_score": "98",
        "assists": "18",
        "field_goals_attempted": "77",
        "free_throws_attempted": "20",
        "offensive_rebounds": "10",
        "turnovers": "11",
        "total_rebounds": "41",
        "gp": "8",
        "group_set": "set-b",
        "group_id": "gid-b",
        "group_name": "Lineup B",
        "w": "5",
        "l": "3",
        "w_pct": "0.625",
        "min": "180",
        "pts": "102",
        "plus_minus": "-2",
        "athlete_id": "102",
        "athlete_display_name": "Player Two",
        "minutes": "29:20",
        "rebounds": "7",
        "points": "15",
        "starter": "false",
        "active": "true",
        "did_not_play": "false",
        "official_full_name": "Ref Two",
        "official_display_name": "Ref Two",
        "official_position": "Referee",
        "official_position_id": "2",
        "official_order": "2",
        "type_id": "2",
        "type_text": "foul",
        "text": "Personal foul",
        "clock_display_value": "10:00",
        "score_value": "1",
        "scoring_play": "false",
        "period_number": "2",
        "period_display_value": "Q2",
        "coordinate_x": "12",
        "coordinate_y": "8",
        "coordinate_x_raw": "12",
        "coordinate_y_raw": "8",
    },
]


def _fake_release_fetch(*args, **kwargs):
    return {
        "ok": True,
        "status": "ok",
        "record_count": len(FAKE_RELEASE_ROWS),
        "records": FAKE_RELEASE_ROWS,
        "fieldnames": list(FAKE_RELEASE_ROWS[0].keys()),
    }


def _fake_page_fetch(*args, **kwargs):
    return {"ok": True, "status": "ok", "text": "<html><body>public page</body></html>", "text_length": 36}


class TestBasketballOxylabsAudit(unittest.TestCase):
    def test_source_exhaustion_log_classifies_lane_states(self):
        with patch("automation_scheduler.basketball_oxylabs_audit.basketball_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.basketball_oxylabs_audit.build_basketball_source_exhaustion_query_plan",
            return_value={"lane_query_index": FAKE_QUERY_INDEX},
        ), patch("automation_scheduler.basketball_oxylabs_audit.fetch_release_asset_rows", side_effect=_fake_release_fetch), patch(
            "automation_scheduler.basketball_oxylabs_audit.fetch_public_page_text",
            side_effect=_fake_page_fetch,
        ):
            report = build_basketball_oxylabs_source_exhaustion_log()

        self.assertTrue(report["ok"])
        self.assertEqual(report["source_candidate_count"], len(FAKE_LANES))
        self.assertEqual(report["lanes_tested_count"], len(FAKE_LANES))
        self.assertTrue(report["oxylabs_residential_proxy_used"])
        self.assertTrue(report["oxylabs_web_scraper_api_used"])
        self.assertEqual(report["lanes_free_open_backfilled"], 2)
        self.assertEqual(report["lanes_manual_import_required"], 1)
        self.assertEqual(report["lanes_paid_subscription_required"], 1)
        self.assertEqual(report["lanes_policy_blocked"], 1)
        self.assertEqual(report["lanes_with_vague_status"], 0)
        states = {row["lane_name"]: row["final_actionable_state"] for row in report["source_candidate_rows"]}
        self.assertEqual(states["schedule_results"], "free_open_backfilled")
        self.assertEqual(states["lineup_on_off"], "free_open_backfilled")
        self.assertEqual(states["strength_of_schedule_context"], "manual_import_required")
        self.assertEqual(states["injuries_availability"], "paid_subscription_required")
        self.assertEqual(states["restricted_reference_tables"], "policy_blocked")

    def test_writer_creates_report_files(self):
        with patch("automation_scheduler.basketball_oxylabs_audit.basketball_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.basketball_oxylabs_audit.build_basketball_source_exhaustion_query_plan",
            return_value={"lane_query_index": FAKE_QUERY_INDEX},
        ), patch("automation_scheduler.basketball_oxylabs_audit.fetch_release_asset_rows", side_effect=_fake_release_fetch), patch(
            "automation_scheduler.basketball_oxylabs_audit.fetch_public_page_text",
            side_effect=_fake_page_fetch,
        ):
            report = build_basketball_oxylabs_source_exhaustion_log()

        with tempfile.TemporaryDirectory() as tmp:
            paths = write_basketball_oxylabs_source_exhaustion_log(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
