import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.mlb_cutoff_date_features import (
    build_cutoff_date_context,
    build_cutoff_feature_report,
    build_game_cutoff_snapshot,
    build_player_cutoff_snapshot,
    build_team_cutoff_snapshot,
    filter_records_by_cutoff_date,
    validate_no_future_data_used,
    write_cutoff_feature_report,
)


def _seed_latest(base, source_id, rows, *, fields=None, seasons=("2025",)):
    fields = list(fields or sorted({key for row in rows for key in row.keys()}))
    path = Path(base) / "data_sources" / "mlb_open_data" / "validated" / source_id / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "records_validated": len(rows),
                "fields_available": fields,
                "field_types": {field: "string" for field in fields},
                "seasons_available": list(seasons),
                "seasons_backfilled": list(seasons),
                "sample_rows": rows,
                "validated_rows": rows,
            }
        ),
        encoding="utf-8",
    )


class TestMlbCutoffDateFeatures(unittest.TestCase):
    def test_cutoff_context_requires_valid_inputs(self):
        with self.assertRaises(ValueError):
            build_cutoff_date_context(season=None, cutoff_date="2025-06-01")
        with self.assertRaises(ValueError):
            build_cutoff_date_context(season="2025", cutoff_date=None)

    def test_cutoff_filter_excludes_future_and_postseason_rows(self):
        context = build_cutoff_date_context(season="2025", cutoff_date="2025-06-15")
        rows = [
            {"event_date": "2025-06-01", "game_type": "R"},
            {"event_date": "2025-06-20", "game_type": "R"},
            {"event_date": "2025-10-10", "game_type": "POST"},
        ]
        filtered = filter_records_by_cutoff_date(rows, context)
        self.assertEqual(filtered["kept_count"], 1)
        self.assertEqual(filtered["excluded_future"], 1)
        self.assertEqual(filtered["excluded_postseason"], 1)
        self.assertTrue(validate_no_future_data_used(filtered["kept"], context))

    def test_cutoff_report_blocks_sensitive_groups_without_explicit_allow(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(
                tmp,
                "team_stats_lahman",
                rows=[{"season": "2025", "event_date": "2025-06-01", "teamID": "NYY", "R": 5, "RA": 3, "W": 1, "L": 0}],
            )
            _seed_latest(
                tmp,
                "bullpen_usage_mlb_stats_api",
                rows=[{"season": "2025", "event_date": "2025-06-01", "game_pk": "1", "team_id": "NYY", "player_id": "p1", "pitch_count": 20, "innings_pitched": 2}],
            )
            report = build_cutoff_feature_report(
                season="2025",
                cutoff_date="2025-06-15",
                team="NYY",
                source_lanes=["team_game_run_profile", "bullpen_usage"],
                base_data_dir=tmp,
            )
        team = [row for row in report["feature_rows"] if row["feature_group"] == "team_game_run_profile"][0]
        bullpen = [row for row in report["feature_rows"] if row["feature_group"] == "bullpen_usage"][0]
        self.assertEqual(team["status"], "available")
        self.assertEqual(team["provenance"]["max_date_used"], "2025-06-01")
        self.assertTrue(report["no_future_data_used"])
        self.assertEqual(bullpen["status"], "blocked")
        self.assertEqual(bullpen["blocked_reason"], "cutoff_sensitive_field_requires_explicit_allow")
        self.assertIn("team_game_run_profile", report["feature_groups_available"])
        self.assertIn("bullpen_usage", report["feature_groups_blocked"])

    def test_cutoff_report_excludes_postseason_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(
                tmp,
                "postseason_labels_retrosheet",
                rows=[{"season": "2025", "event_date": "2025-10-10", "game_id": "g1", "game_type": "POST", "playoff_round": "WS"}],
            )
            report = build_cutoff_feature_report(
                season="2025",
                cutoff_date="2025-10-15",
                source_lanes=["postseason_context"],
                base_data_dir=tmp,
            )
        postseason = report["feature_rows"][0]
        self.assertEqual(postseason["status"], "blocked")
        self.assertEqual(postseason["blocked_reason"], "no_cutoff_eligible_records_available")
        self.assertEqual(report["team_snapshot_count"], 0)
        self.assertEqual(report["player_snapshot_count"], 0)

    def test_snapshot_helpers_write_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(
                tmp,
                "team_stats_lahman",
                rows=[{"season": "2025", "event_date": "2025-06-01", "teamID": "NYY", "R": 5, "RA": 3, "W": 1, "L": 0}],
            )
            report = build_cutoff_feature_report(
                season="2025",
                cutoff_date="2025-06-15",
                team="NYY",
                source_lanes=["team_game_run_profile"],
                base_data_dir=tmp,
            )
            paths = write_cutoff_feature_report(report, base_data_dir=tmp)
            team_snapshot = build_team_cutoff_snapshot(
                build_cutoff_date_context(season="2025", cutoff_date="2025-06-15", team="NYY", source_lanes=["team_game_run_profile"]),
                base_data_dir=tmp,
            )
            player_snapshot = build_player_cutoff_snapshot(
                build_cutoff_date_context(season="2025", cutoff_date="2025-06-15", player_id="p1", source_lanes=["batting_profile"]),
                base_data_dir=tmp,
            )
            game_snapshot = build_game_cutoff_snapshot(
                build_cutoff_date_context(season="2025", cutoff_date="2025-06-15", source_lanes=["postseason_context"]),
                base_data_dir=tmp,
            )
            latest = Path(tmp, paths["latest_json_path"])
            self.assertTrue(latest.exists())
        self.assertIn("data_sources/mlb_open_data/cutoff_date_features/latest.json", paths["latest_json_path"])
        self.assertTrue(team_snapshot)
        self.assertIsInstance(player_snapshot, list)
        self.assertIsInstance(game_snapshot, list)


if __name__ == "__main__":
    unittest.main()
