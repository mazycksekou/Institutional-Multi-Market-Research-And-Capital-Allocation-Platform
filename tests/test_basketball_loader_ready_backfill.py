import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.basketball_loader_ready_backfill import (
    build_basketball_loader_ready_backfill_report,
    write_basketball_loader_ready_backfill_report,
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
]

FAKE_RELEASE_ROWS = [
    {
        "game_id": "g1",
        "season": "2025",
        "game_date": "2025-01-01",
        "team_id": "1",
        "team_display_name": "Team A",
        "team_abbreviation": "A",
        "group_set": "set-a",
        "group_id": "gid-a",
        "group_name": "Lineup A",
        "gp": "10",
        "w": "7",
        "l": "3",
        "w_pct": "0.7",
        "min": "250",
        "pts": "110",
        "plus_minus": "8",
        "starter": "true",
        "active": "true",
        "did_not_play": "false",
        "athlete_id": "101",
        "athlete_display_name": "Player One",
        "minutes": "32:10",
        "rebounds": "8",
        "points": "18",
        "assists": "5",
        "turnovers": "2",
        "field_goals_attempted": "15",
        "free_throws_attempted": "4",
        "offensive_rebounds": "1",
        "team_turnovers": "2",
        "total_rebounds": "44",
        "official_full_name": "Ref One",
        "official_display_name": "Ref One",
        "official_position": "Crew Chief",
        "official_position_id": "1",
        "official_order": "1",
    },
    {
        "game_id": "g2",
        "season": "2025",
        "game_date": "2025-01-02",
        "team_id": "2",
        "team_display_name": "Team B",
        "team_abbreviation": "B",
        "group_set": "set-b",
        "group_id": "gid-b",
        "group_name": "Lineup B",
        "gp": "8",
        "w": "5",
        "l": "3",
        "w_pct": "0.625",
        "min": "180",
        "pts": "102",
        "plus_minus": "-2",
        "starter": "false",
        "active": "true",
        "did_not_play": "false",
        "athlete_id": "102",
        "athlete_display_name": "Player Two",
        "minutes": "29:20",
        "rebounds": "7",
        "points": "15",
        "assists": "4",
        "turnovers": "1",
        "field_goals_attempted": "12",
        "free_throws_attempted": "5",
        "offensive_rebounds": "2",
        "team_turnovers": "1",
        "total_rebounds": "41",
        "official_full_name": "Ref Two",
        "official_display_name": "Ref Two",
        "official_position": "Referee",
        "official_position_id": "2",
        "official_order": "2",
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


class TestBasketballLoaderReadyBackfill(unittest.TestCase):
    def test_loader_ready_backfill_report_closes_loader_ready_lanes(self):
        with patch("automation_scheduler.basketball_loader_ready_backfill.basketball_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.basketball_loader_ready_backfill.fetch_release_asset_rows",
            side_effect=_fake_release_fetch,
        ), tempfile.TemporaryDirectory() as tmp:
            with patch("automation_scheduler.basketball_loader_ready_backfill.BASKETBALL_DATA_ROOT", Path(tmp) / "data_sources" / "basketball_open_data"):
                report = build_basketball_loader_ready_backfill_report()

        self.assertTrue(report["ok"])
        self.assertEqual(report["loader_ready_lanes_before"], 2)
        self.assertEqual(report["loader_ready_lanes_backfilled"], 2)
        self.assertEqual(report["loader_ready_lanes_hard_blocked"], 0)
        self.assertEqual(report["fields_closed_this_pass"], 7)
        self.assertEqual(report["fields_reclassified_this_pass"], 1)
        self.assertEqual(report["records_added_by_sport"]["basketball_nba"], 2)
        self.assertEqual(report["records_added_by_sport"]["basketball_wnba"], 2)
        lane_states = {row["lane_name"]: row["final_actionable_state"] for row in report["backfill_rows"]}
        self.assertEqual(lane_states["schedule_results"], "free_open_backfilled")
        self.assertEqual(lane_states["lineup_on_off"], "free_open_backfilled")

    def test_writer_creates_report_files(self):
        with patch("automation_scheduler.basketball_loader_ready_backfill.basketball_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.basketball_loader_ready_backfill.fetch_release_asset_rows",
            side_effect=_fake_release_fetch,
        ), tempfile.TemporaryDirectory() as tmp:
            with patch("automation_scheduler.basketball_loader_ready_backfill.BASKETBALL_DATA_ROOT", Path(tmp) / "data_sources" / "basketball_open_data"):
                report = build_basketball_loader_ready_backfill_report()
            paths = write_basketball_loader_ready_backfill_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
