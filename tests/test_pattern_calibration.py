import unittest

from src.services.streamlit_dashboard_facade import record_micro_outcome_windows, supports_outcome_window
from src.services.streamlit_dashboard_facade import build_pattern_calibration_report, calculate_performance_metrics, record_trade_outcome_windows
from src.automation_scheduler_legacy.response_compactor import compact_micro_outcome_calibration_response


class TestPatternCalibration(unittest.TestCase):
    def _detection(self):
        return {
            "detection_id": "d1",
            "asset_symbol": "TEST",
            "asset_type": "stock",
            "timeframe": "5m",
            "pattern_id": "opening_range_breakout",
            "detected_at": "2026-06-01T13:30:00+00:00",
            "entry_reference_price": 10.0,
            "entry_trigger_price": 10.1,
            "target_price": 11.0,
            "stop_loss_level": 9.5,
            "direction": "bullish",
            "session_time_bucket": "OPENING_DRIVE",
            "liquidity_tier": "strong",
            "price_band": "preferred_3_to_12",
            "catalyst_type": "earnings",
            "balance_sheet_risk_bucket": "low",
        }

    def _history(self):
        return [
            {"offset_seconds": 15, "price": 10.15, "high": 10.2, "low": 9.95, "volume": 1000, "spread_percent": 0.2, "liquidity_score": 80},
            {"offset_seconds": 30, "price": 10.4, "high": 10.45, "low": 10.05, "volume": 1400, "spread_percent": 0.2, "liquidity_score": 82},
            {"offset_seconds": 60, "price": 10.7, "high": 10.8, "low": 10.1, "volume": 1700, "spread_percent": 0.25, "liquidity_score": 82},
            {"offset_seconds": 300, "price": 11.05, "high": 11.1, "low": 10.2, "volume": 2200, "spread_percent": 0.25, "liquidity_score": 84},
        ]

    def test_resolution_support_rules(self):
        self.assertFalse(supports_outcome_window("5m_candles", "1m"))
        self.assertFalse(supports_outcome_window("1m_candles", "15s"))
        self.assertTrue(supports_outcome_window("1m_candles", "1m"))
        self.assertTrue(supports_outcome_window("sub_minute", "15s"))

    def test_micro_outcome_recording_and_insufficient_resolution(self):
        report = record_micro_outcome_windows(self._detection(), self._history(), data_resolution="sub_minute")
        self.assertEqual(report["record_count"], 5)
        first = next(row for row in report["records"] if row["outcome_window"] == "15s")
        self.assertEqual(first["outcome_status"], "settled")
        coarse = record_micro_outcome_windows(self._detection(), self._history(), data_resolution="5m_candles")
        self.assertEqual(coarse["status_counts"]["data_insufficient"], 5)
        self.assertIn("15s", coarse["unsupported_windows"])
        self.assertIn("1m", coarse["unsupported_windows"])

    def test_unsupported_subminute_differs_from_delayed_measured(self):
        coarse = record_micro_outcome_windows(
            self._detection(),
            [{"offset_seconds": 45, "price": 10.4, "high": 10.45, "low": 10.0}],
            data_resolution="1m_candles",
            windows=("15s",),
        )
        unsupported = coarse["records"][0]
        self.assertEqual(unsupported["outcome_status"], "data_insufficient")
        self.assertTrue(unsupported["data_resolution_insufficient"])
        self.assertFalse(unsupported["usable_for_calibration"])

        delayed = record_micro_outcome_windows(
            self._detection(),
            [{"offset_seconds": 45, "price": 10.4, "high": 10.45, "low": 10.0, "delay_source": "late_quote"}],
            data_resolution="sub_minute",
            windows=("15s",),
        )
        measured = delayed["records"][0]
        self.assertEqual(measured["outcome_status"], "delayed_measured")
        self.assertFalse(measured["data_resolution_insufficient"])
        self.assertEqual(measured["requested_window_seconds"], 15)
        self.assertEqual(measured["effective_window_seconds"], 45)
        self.assertEqual(measured["delayed_by_seconds"], 30)
        self.assertEqual(measured["delay_source"], "late_quote")
        self.assertTrue(measured["usable_for_calibration"])

    def test_delayed_pending_fields(self):
        pending = record_micro_outcome_windows(self._detection(), [], data_resolution="sub_minute", windows=("15s",))
        row = pending["records"][0]
        self.assertEqual(row["outcome_status"], "delayed_pending")
        self.assertEqual(row["requested_window_seconds"], 15)
        self.assertIsNone(row["effective_window_seconds"])
        self.assertEqual(row["delay_source"], "awaiting_price_history")
        self.assertFalse(row["usable_for_calibration"])

    def test_delayed_outcome_fields_persist_compactly(self):
        delayed = record_micro_outcome_windows(
            self._detection(),
            [{"offset_seconds": 45, "price": 10.4, "high": 10.45, "low": 10.0, "delay_source": "late_quote"}],
            data_resolution="sub_minute",
            windows=("15s",),
        )
        compact = compact_micro_outcome_calibration_response(delayed)
        row = compact["records"][0]
        self.assertEqual(row["outcome_status"], "delayed_measured")
        self.assertEqual(row["requested_window_seconds"], 15)
        self.assertEqual(row["effective_window_seconds"], 45)
        self.assertEqual(row["delayed_by_seconds"], 30)
        self.assertEqual(row["delay_source"], "late_quote")
        self.assertTrue(row["usable_for_calibration"])

    def test_normal_outcome_window_recording(self):
        report = record_trade_outcome_windows(self._detection(), self._history(), data_resolution="1m_candles")
        five = next(row for row in report["records"] if row["outcome_window"] == "5m")
        self.assertEqual(five["outcome_status"], "settled")
        self.assertTrue(five["hit_target"])

    def test_calibration_segmentation_by_data_resolution(self):
        record = record_trade_outcome_windows(self._detection(), self._history(), data_resolution="1m_candles")["records"][0]
        report = build_pattern_calibration_report([record])
        self.assertEqual(report["status"], "insufficient_data")
        self.assertTrue(report["insufficient_sample"])
        self.assertTrue(any("1m_candles" in key for key in report["segments"]))

    def test_performance_metrics_do_not_fabricate_sample(self):
        empty = calculate_performance_metrics([])
        self.assertTrue(empty["insufficient_sample"])
        self.assertEqual(empty["total_number_of_trades"], 0)
        rows = [{"outcome_status": "settled", "profit_loss": 2}, {"outcome_status": "settled", "profit_loss": -1}]
        metrics = calculate_performance_metrics(rows)
        self.assertEqual(metrics["total_gain_loss"], 1)
        self.assertEqual(metrics["total_number_of_trades"], 2)
        self.assertTrue(metrics["insufficient_sample"])


if __name__ == "__main__":
    unittest.main()
