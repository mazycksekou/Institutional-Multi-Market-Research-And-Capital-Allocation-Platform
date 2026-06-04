import tempfile
import unittest
from pathlib import Path

from automation_scheduler.mlb_completion_report import build_mlb_completion_report, write_mlb_completion_report


def _seed_latest(base, source_id, *, fields, records=25, seasons=("2024", "2025")):
    path = Path(base) / "data_sources" / "mlb_open_data" / "validated" / source_id / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        __import__("json").dumps(
            {
                "ok": True,
                "status": "full_backfill_complete",
                "records_validated": records,
                "records_rejected": 0,
                "fields_available": list(fields),
                "field_types": {field: "string" for field in fields},
                "seasons_available": list(seasons),
                "seasons_backfilled": list(seasons),
                "sample_rows": [{field: f"{field}-value" for field in fields}],
                "validated_rows": [{field: f"{field}-value" for field in fields}],
                "date_coverage": {"earliest_observed": "2024-04-01", "latest_observed": "2025-09-30"},
            }
        ),
        encoding="utf-8",
    )


class TestMlbCompletionReport(unittest.TestCase):
    def test_report_exposes_required_fields_and_safety_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            _seed_latest(tmp, "team_stats_lahman", fields=["yearID", "teamID", "R", "RA"])
            _seed_latest(tmp, "batting_stats_lahman", fields=["playerID", "yearID", "AB", "H", "HR", "BB", "SO"])
            _seed_latest(tmp, "pitching_stats_lahman", fields=["playerID", "yearID", "ERA", "G", "GS", "IPouts"])
            report = build_mlb_completion_report(base_data_dir=tmp, run_mode="open_free_mode", tests_run=["one"], tests_passed=["one"], commit_hash="abc123")
            paths = write_mlb_completion_report(report, output_dir=Path(tmp) / "reports")

        for key in (
            "sport",
            "run_mode",
            "started_at",
            "completed_at",
            "source_families_audited",
            "source_families_approved",
            "source_families_populated",
            "source_families_blocked",
            "source_families_research",
            "record_count_total",
            "rejected_count_total",
            "season_coverage",
            "date_coverage",
            "feature_groups_built",
            "feature_groups_model_eligible",
            "feature_groups_blocked",
            "cutoff_safe_feature_count",
            "future_leakage_checks_passed",
            "tests_run",
            "tests_passed",
            "provider_write",
            "execution_allowed",
            "execution_allowed_count",
            "live_execution_enabled",
            "auto_execution_enabled",
            "kalshi_order_execution_enabled",
            "sportsbook_bet_execution_enabled",
            "broker_order_execution_enabled",
            "stock_trade_execution_enabled",
            "crypto_trade_execution_enabled",
            "actual_orders_submitted",
            "actual_bets_submitted",
            "actual_trades_submitted",
            "actual_crypto_swaps_submitted",
            "raw_payload_included",
            "raw_html_persisted",
            "raw_screenshot_persisted",
            "secrets_included",
            "enabled_source_count",
            "paid_source_enabled_count",
            "blockers",
            "fallbacks_used",
            "commit_hash",
        ):
            self.assertIn(key, report)
        self.assertTrue(report["ok"])
        self.assertEqual(report["run_mode"], "open_free_mode")
        self.assertTrue(report["started_at"])
        self.assertTrue(report["completed_at"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["enabled_source_count"], 0)
        self.assertEqual(report["paid_source_enabled_count"], 0)
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["raw_screenshot_persisted"])
        self.assertFalse(report["secrets_included"])
        self.assertTrue(paths["latest_json_path"].endswith("reports/MLB_COMPLETION_FINAL_REPORT.json"))
        self.assertTrue(paths["latest_markdown_path"].endswith("reports/MLB_COMPLETION_FINAL_REPORT.md"))

    def test_paid_mode_flag_toggles_paid_source_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_mlb_completion_report(
                base_data_dir=tmp,
                run_mode="open_free_mode",
                allow_oxylabs=True,
                allow_paid_retrieval=True,
            )
        self.assertEqual(report["run_mode"], "open_free_mode")
        self.assertEqual(report["paid_source_enabled_count"], 1)

    def test_report_includes_feature_and_source_tables(self):
        report = build_mlb_completion_report()
        self.assertIsInstance(report["source_family_table"], list)
        self.assertTrue(report["source_family_table"])
        self.assertTrue(report["feature_groups_built"] or report["feature_groups_model_eligible"])
        self.assertIn("derived_feature_report", report)


if __name__ == "__main__":
    unittest.main()
