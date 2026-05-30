import tempfile
import unittest
from pathlib import Path

from automation_scheduler.institutional_cross_asset_reports import build_daily_report_payload, render_markdown_report, write_daily_report


class TestInstitutionalCrossAssetReports(unittest.TestCase):
    def test_daily_report_contains_required_safety_fields(self):
        run = {
            "run_id": "run-1",
            "created_at": "2026-05-30T12:00:00+00:00",
            "records_read": 1,
            "records_normalized": 1,
            "source_counts": {"prediction_market": 1},
            "records": [{"asset_class": "prediction_market", "reason_codes": ["wide_spread"], "outcome_status": "pending"}],
            "calibration": {
                "next_required_data": ["more_explicit_outcomes"],
                "asset_classes": {
                    "prediction_market": {"status": "partial_calibration", "matched_outcomes_count": 1, "insufficient_sample": True},
                    "stock": {"status": "insufficient_data", "matched_outcomes_count": 0, "insufficient_sample": True},
                    "bond": {"status": "insufficient_data", "matched_outcomes_count": 0, "insufficient_sample": True},
                    "major_asset": {"status": "insufficient_data", "matched_outcomes_count": 0, "insufficient_sample": True},
                    "sportsbook": {"status": "insufficient_data", "matched_outcomes_count": 0, "insufficient_sample": True},
                },
            },
            "execution_simulation": {"execution_desk_status": "simulation_only", "simulated_ticket_created": False},
            "deepseek_review": {"status": "disabled"},
        }
        report = build_daily_report_payload(run)
        self.assertEqual(report["actual_orders_submitted"], 0)
        self.assertEqual(report["actual_bets_submitted"], 0)
        self.assertEqual(report["actual_trades_submitted"], 0)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["live_execution_enabled"])
        self.assertEqual(report["prediction_market_status"], "partial_calibration")
        self.assertIn("more_explicit_outcomes", report["next_required_data"])

    def test_write_daily_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = write_daily_report(
                {
                    "run_id": "run-1",
                    "created_at": "2026-05-30T12:00:00+00:00",
                    "records": [],
                    "calibration": {"asset_classes": {}, "next_required_data": []},
                    "execution_simulation": {},
                    "deepseek_review": {},
                },
                base_data_dir=tmp,
            )
            json_path = Path(tmp) / result["daily_report_path"]
            md_path = Path(tmp) / result["daily_markdown_path"]
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            self.assertTrue(str(json_path).endswith(".json"))
            self.assertTrue(str(md_path).endswith(".md"))

    def test_markdown_is_compact(self):
        text = render_markdown_report({"date": "2026-05-30", "run_id": "r1", "next_required_data": ["x"]})
        self.assertIn("provider_write: false", text)
        self.assertIn("execution_allowed: false", text)


if __name__ == "__main__":
    unittest.main()
