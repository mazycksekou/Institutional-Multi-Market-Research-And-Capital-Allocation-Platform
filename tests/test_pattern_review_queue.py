import tempfile
import unittest

from automation_scheduler.pattern_review_queue import (
    build_pattern_review_item,
    load_pattern_review_queue,
    persist_pattern_review_queue,
    queue_status_for_score,
)


class TestPatternReviewQueue(unittest.TestCase):
    def _base_inputs(self):
        detection = {
            "detection_id": "d1",
            "asset_symbol": "TEST",
            "asset_type": "stock",
            "timeframe": "5m",
            "pattern_id": "bull_flag_breakout",
            "pattern_name": "bull_flag_breakout",
            "pattern_family": "momentum",
            "direction": "bullish",
            "detected_at": "2026-06-01T14:35:00+00:00",
            "pattern_quality_score": 88,
            "volume_confirmation_score": 86,
            "breakout_confirmation_score": 82,
            "entry_trigger_price": 10,
            "stop_loss_level": 9.5,
            "target_price": 11.5,
        }
        liquidity = {"liquidity_score": 82, "liquidity_tier": "strong", "spread_slippage_score": 88, "liquidity_blockers": []}
        catalyst = {"catalyst_detected": True, "catalyst_type": "earnings", "catalyst_quality_score": 84}
        time_context = {"session_time_bucket": "OPENING_DRIVE", "time_of_day_edge_score": 92}
        risk_reward = {"risk_reward_permission_status": "VALID", "risk_reward_score": 86, "reward_risk_ratio": 3.0, "breakeven_win_rate": 0.25}
        balance = {"balance_sheet_quality_score": 75, "fundamental_risk_score": 25, "balance_sheet_risk_bucket": "low", "data_insufficient": False}
        price_band = {"price": 10, "price_band": "preferred_3_to_12", "price_range_quality_score": 94, "small_account_fit_score": 94, "overextension_risk": 15, "no_review_reasons": []}
        session = {"session_permission_status": "ALLOW_REVIEW", "session_risk_score": 95, "walk_away_reasons": []}
        quality = {"stock_quality_score": 88, "a_quality_candidate": True}
        return detection, liquidity, catalyst, time_context, risk_reward, balance, price_band, session, quality

    def test_threshold_behavior(self):
        self.assertEqual(queue_status_for_score(85), "ACTIVE_REVIEW")
        self.assertEqual(queue_status_for_score(70), "WATCHLIST_REVIEW")
        self.assertEqual(queue_status_for_score(55), "LOW_PRIORITY_REVIEW")
        self.assertEqual(queue_status_for_score(54.9), "NO_REVIEW")

    def test_high_quality_candidate_becomes_watch_or_active(self):
        item = build_pattern_review_item(
            detection=self._base_inputs()[0],
            liquidity=self._base_inputs()[1],
            catalyst=self._base_inputs()[2],
            time_context=self._base_inputs()[3],
            risk_reward=self._base_inputs()[4],
            balance_sheet=self._base_inputs()[5],
            price_band=self._base_inputs()[6],
            session_risk=self._base_inputs()[7],
            quality=self._base_inputs()[8],
            historical_calibration_score=70,
            micro_calibration_score=70,
            trade_window_calibration_score=70,
        )
        self.assertIn(item["queue_status"], {"WATCHLIST_REVIEW", "ACTIVE_REVIEW"})
        self.assertFalse(item["execution_allowed"])
        self.assertIn("liquidity_confirmed", item["review_reasons"])

    def test_low_liquidity_forces_no_trade_without_special_catalyst(self):
        args = self._base_inputs()
        low_liquidity = dict(args[1], liquidity_score=25, liquidity_blockers=["liquidity_score_below_40"])
        item = build_pattern_review_item(
            detection=args[0],
            liquidity=low_liquidity,
            catalyst=args[2],
            time_context=args[3],
            risk_reward=args[4],
            balance_sheet=args[5],
            price_band=args[6],
            session_risk=args[7],
            quality=args[8],
        )
        self.assertEqual(item["queue_status"], "NO_TRADE")
        self.assertIn("liquidity_score_below_40", item["no_trade_reasons"])

    def test_session_lock_overrides_review(self):
        args = self._base_inputs()
        session = {"session_permission_status": "NO_TRADE_SESSION_LOCK", "session_risk_score": 0, "walk_away_reasons": ["daily_giveback_limit_reached"]}
        item = build_pattern_review_item(
            detection=args[0],
            liquidity=args[1],
            catalyst=args[2],
            time_context=args[3],
            risk_reward=args[4],
            balance_sheet=args[5],
            price_band=args[6],
            session_risk=session,
            quality=args[8],
        )
        self.assertEqual(item["queue_status"], "NO_TRADE_SESSION_LOCK")

    def test_queue_persistence_is_local_and_safe(self):
        args = self._base_inputs()
        item = build_pattern_review_item(
            detection=args[0],
            liquidity=args[1],
            catalyst=args[2],
            time_context=args[3],
            risk_reward=args[4],
            balance_sheet=args[5],
            price_band=args[6],
            session_risk=args[7],
            quality=args[8],
        )
        item["api_key"] = "secret"
        item["raw_payload"] = {"drop": True}
        with tempfile.TemporaryDirectory() as tmp:
            persist_pattern_review_queue([item], base_data_dir=tmp)
            loaded = load_pattern_review_queue(base_data_dir=tmp)
        rendered = str(loaded)
        self.assertEqual(loaded["count"], 1)
        self.assertFalse(loaded["items"][0]["execution_allowed"])
        self.assertNotIn("secret", rendered)
        self.assertNotIn("raw_payload", rendered)


if __name__ == "__main__":
    unittest.main()
