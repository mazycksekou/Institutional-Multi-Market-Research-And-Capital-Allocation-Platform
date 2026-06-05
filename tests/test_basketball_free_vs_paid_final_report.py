import tempfile
import unittest
from pathlib import Path

from automation_scheduler.basketball_free_vs_paid_readiness import build_and_write_all_basketball_reports, build_basketball_final_report


class TestBasketballFreeVsPaidFinalReport(unittest.TestCase):
    def test_final_report_contains_requested_verdicts_and_safety(self):
        report = build_basketball_final_report()
        self.assertTrue(report["ok"])
        self.assertEqual(report["overall_basketball_verdict"], "BASKETBALL_FREE_VS_PAID_COMPLETE")
        for key in ("NBA_verdict", "WNBA_verdict", "NCAAB_verdict", "NCAAW_verdict"):
            self.assertTrue(report[key])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["raw_payload_included"])
        self.assertEqual(report["paid_source_enabled_count"], 1)

    def test_writer_creates_required_reports_and_manual_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "reports"
            result = build_and_write_all_basketball_reports(run_live_samples=False, output_dir=output)
            self.assertTrue(Path(result["paths"]["final"]["latest_json_path"]).exists())
            self.assertTrue(Path(result["paths"]["data_calibration_readiness"]["latest_json_path"]).exists())
            self.assertTrue(Path(result["paths"]["paid_data_requirement_matrix"]["latest_json_path"]).exists())


if __name__ == "__main__":
    unittest.main()
