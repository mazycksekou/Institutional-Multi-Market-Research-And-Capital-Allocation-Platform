import json
import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.model_performance_report import write_model_performance_report


class TestModelPerformanceReport(unittest.TestCase):
    def test_compact_vs_full_report(self):
        report = {
            "report_id": "perf_1",
            "model_id": "m1",
            "sample_size": 12,
            "realized_roi_percent": 1.2,
            "average_clv_percent": 0.9,
            "positive_clv_rate": 0.66,
            "max_drawdown_percent": 2.4,
            "brier_score": 0.21,
            "calibration_status": "backtest_complete",
            "performance_status": "backtest_complete",
            "blocked_reasons": [],
            "recommended_next_action": "watch_recheck",
            "status": "backtest_complete",
        }
        with TemporaryDirectory() as tmp:
            result = write_model_performance_report(report, base_dir=tmp)
            with open(result["report_path"], "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertIn("model_id", payload)
            self.assertIn("report_path", result["compact_report"])
            self.assertNotIn("full_report", result["compact_report"])


if __name__ == "__main__":
    unittest.main()

