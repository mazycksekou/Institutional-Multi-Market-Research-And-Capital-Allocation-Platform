import json
import tempfile
import unittest
from pathlib import Path

from automation_scheduler.local_sports_history_audit import (
    ALLOWED_BLOCKED_REASONS,
    build_local_sports_history_audit_report,
    write_local_sports_history_audit_report,
)


class TestLocalSportsHistoryAudit(unittest.TestCase):
    def _write_json(self, path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_report_writes_runtime_paths_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            self._write_json(
                root / "nba_results.json",
                {
                    "records": [
                        {
                            "league": "NBA",
                            "event_id": "nba-1",
                            "event_date": "2026-01-01",
                            "home_team": "A",
                            "away_team": "B",
                            "home_score": 101,
                            "away_score": 98,
                        }
                    ]
                },
            )
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])
            paths = write_local_sports_history_audit_report(report, base_data_dir=tmp)
            latest_json = Path(tmp, paths["latest_json_path"])
            latest_md = Path(tmp, paths["latest_markdown_path"])

            self.assertTrue(latest_json.exists())
            self.assertTrue(latest_md.exists())
            markdown_lines = latest_md.read_text(encoding="utf-8").splitlines()

        self.assertIn("data_sources/local_sports_history/latest.json", paths["latest_json_path"])
        self.assertIn("data_sources/local_sports_history/latest.md", paths["latest_markdown_path"])
        self.assertIn("data_sources/local_sports_history/items/", paths["item_json_path"])
        self.assertIn("data_sources/local_sports_history/items/", paths["item_markdown_path"])
        self.assertIn("data_sources/local_sports_history/daily/", paths["daily_json_path"])
        self.assertIn("data_sources/local_sports_history/daily/", paths["daily_markdown_path"])
        self.assertEqual(len([line for line in markdown_lines if line[:2] in {f"{i}." for i in range(1, 9)}]), 8)

    def test_valid_schedule_result_fixture_creates_preview_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            self._write_json(
                root / "ncaaf_schedule_results.json",
                [
                    {
                        "sport": "college football",
                        "game_id": "cfb-1",
                        "game_date": "2025-09-01",
                        "home_team": "Home",
                        "away_team": "Away",
                        "home_points": 28,
                        "away_points": 21,
                    }
                ],
            )
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])

        self.assertEqual(report["usable_tier0_preview_files"], 1)
        self.assertEqual(report["modules_with_preview_rows"], ["americanfootball_ncaaf"])
        self.assertEqual(report["preview_rows"][0]["normalization_status"], "available")
        self.assertEqual(report["preview_rows"][0]["final_margin"], 7.0)
        self.assertEqual(report["preview_rows"][0]["total_score"], 49.0)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_missing_scores_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            self._write_json(
                root / "mlb_schedule.json",
                [{"league": "MLB", "event_id": "mlb-1", "event_date": "2026-04-01", "home_team": "A", "away_team": "B"}],
            )
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])

        self.assertEqual(report["candidate_files"][0]["blocked_reason"], "missing_scores_or_results")
        self.assertEqual(report["usable_tier0_preview_files"], 0)

    def test_missing_dates_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            self._write_json(
                root / "soccer_results.json",
                [{"sport": "soccer", "event_id": "soc-1", "home_team": "A", "away_team": "B", "home_score": 2, "away_score": 1}],
            )
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])

        self.assertEqual(report["candidate_files"][0]["blocked_reason"], "missing_event_date")
        self.assertEqual(report["top_missing_fields"][0]["field"], "event_date")

    def test_malformed_json_is_reported_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            root.mkdir(parents=True)
            (root / "bad.json").write_text("{not-json", encoding="utf-8")
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])

        self.assertEqual(report["candidate_files"][0]["blocked_reason"], "malformed_json")
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_unsupported_shape_reports_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            self._write_json(root / "summary.json", {"status": "ok", "count": 3})
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])

        self.assertEqual(report["candidate_files"][0]["blocked_reason"], "unsupported_shape")

    def test_skips_env_and_secret_like_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            root.mkdir(parents=True)
            (root / ".env").write_text("API_KEY=do-not-leak", encoding="utf-8")
            self._write_json(root / "api_key_fixture.json", {"api_key": "do-not-leak"})
            self._write_json(
                root / "nba_results.json",
                [{"league": "NBA", "event_id": "nba-1", "event_date": "2026-01-01", "home_team": "A", "away_team": "B", "home_score": 90, "away_score": 88}],
            )
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])
            rendered = json.dumps(report, sort_keys=True).lower()

        self.assertEqual(report["files_skipped_secret_like_path_count"], 1)
        self.assertNotIn(".env", rendered)
        self.assertNotIn("do-not-leak", rendered)
        self.assertEqual(report["files_scanned"], 1)

    def test_raw_payload_and_secret_values_are_not_included(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            self._write_json(
                root / "nba_raw.json",
                {
                    "records": [
                        {
                            "league": "NBA",
                            "event_id": "nba-1",
                            "event_date": "2026-01-01",
                            "home_team": "A",
                            "away_team": "B",
                            "home_score": 90,
                            "away_score": 88,
                            "provider_payload": {"secret": "drop"},
                        }
                    ]
                },
            )
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])
            rendered = json.dumps(report, sort_keys=True).lower()

        self.assertEqual(report["candidate_files"][0]["blocked_reason"], "raw_payload_risk")
        self.assertNotIn("provider_payload", rendered)
        self.assertNotIn("drop", rendered)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_safety_contract_has_no_provider_or_persistence_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[Path(tmp) / "missing"])

        self.assertEqual(report["provider_calls_attempted"], 0)
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["outcome_persistence_attempted"])
        self.assertFalse(report["import_or_persist_endpoint_called"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])

    def test_all_file_blocked_reasons_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan"
            self._write_json(root / "summary.json", {"status": "ok"})
            report = build_local_sports_history_audit_report(base_data_dir=tmp, scan_roots=[root])

        reasons = {row["blocked_reason"] for row in report["candidate_files"]}
        self.assertTrue(reasons.issubset(ALLOWED_BLOCKED_REASONS))


if __name__ == "__main__":
    unittest.main()
