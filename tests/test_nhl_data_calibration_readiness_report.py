import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_free_open_exhaustion import build_nhl_data_calibration_readiness_report, write_nhl_data_calibration_readiness_report


class TestNhlDataCalibrationReadinessReport(unittest.TestCase):
    def test_readiness_report_returns_model_row(self):
        report = build_nhl_data_calibration_readiness_report(
            inventory_report={"fields_missing_count": 10},
            source_ledger={
                "source_ledger_rows": [
                    {"lane_name": "schedule_results", "free_or_paid_category": "free_open_populated"},
                    {"lane_name": "injuries_availability", "free_or_paid_category": "free_open_manual_import_needed"},
                    {"lane_name": "goalie_gsaax_dataset", "free_or_paid_category": "paid_data_subscription_required"},
                ]
            },
            audit_report={"lanes_improved_by_oxylabs": 2, "lanes_with_vague_status": 0},
            backfill_report={"records_added_by_nhl": 5, "loader_ready_lanes_backfilled": 2},
            paid_matrix={"requirement_rows": [{"lane_name": "goalie_gsaax_dataset"}]},
        )
        self.assertTrue(report["ok"])
        model = report["models"][0]
        self.assertIn(model["recommendation"], {"ready_but_paid_data_would_improve", "manual_import_needed"})
        self.assertGreater(model["calibration_readiness_score"], 0)

    def test_writer_creates_files(self):
        report = {"models": [{"model": "poisson_bivariate_goalie_special_teams_model", "records_added_this_pass": 1, "loader_ready_lanes_backfilled": 1, "fields_still_missing": 2, "calibration_readiness_score": 75, "recommendation": "ready_but_paid_data_would_improve"}]}
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_data_calibration_readiness_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
