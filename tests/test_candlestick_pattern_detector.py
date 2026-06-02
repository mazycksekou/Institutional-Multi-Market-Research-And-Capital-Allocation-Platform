import unittest

from automation_scheduler.candlestick_pattern_detector import detect_candlestick_patterns, get_pattern_catalog


class TestCandlestickPatternDetector(unittest.TestCase):
    def test_catalog_contains_requested_major_patterns(self):
        catalog = get_pattern_catalog()
        for pattern_id in (
            "opening_range_breakout",
            "gap_and_go",
            "vwap_reclaim",
            "bull_flag_breakout",
            "bullish_engulfing",
            "bearish_engulfing",
            "hammer",
            "doji",
            "failed_breakout",
        ):
            self.assertIn(pattern_id, catalog)

    def test_detects_bullish_engulfing_without_trade_permission(self):
        detections = detect_candlestick_patterns(
            [
                {"open": 10.0, "high": 10.1, "low": 9.4, "close": 9.5, "volume": 1000},
                {"open": 9.4, "high": 10.4, "low": 9.3, "close": 10.3, "volume": 3000},
            ],
            {"asset_symbol": "TEST", "asset_type": "stock", "timeframe": "5m"},
        )
        ids = {row["pattern_id"] for row in detections}
        self.assertIn("bullish_engulfing", ids)
        item = next(row for row in detections if row["pattern_id"] == "bullish_engulfing")
        self.assertFalse(item["execution_allowed"])
        self.assertTrue(item["review_only"])

    def test_detects_opening_range_breakout_and_vwap_reclaim(self):
        detections = detect_candlestick_patterns(
            [
                {"open": 9.8, "high": 10.0, "low": 9.5, "close": 9.7, "volume": 1200},
                {"open": 9.7, "high": 10.8, "low": 9.6, "close": 10.6, "volume": 4200},
            ],
            {
                "asset_symbol": "TEST",
                "asset_type": "stock",
                "timeframe": "5m",
                "opening_range_high": 10.0,
                "vwap": 10.0,
            },
        )
        ids = {row["pattern_id"] for row in detections}
        self.assertIn("opening_range_breakout", ids)
        self.assertIn("vwap_reclaim", ids)


if __name__ == "__main__":
    unittest.main()
