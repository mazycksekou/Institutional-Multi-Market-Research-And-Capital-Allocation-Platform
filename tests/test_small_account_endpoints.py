import unittest

from fastapi.testclient import TestClient

from main import app


class TestSmallAccountEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _review_item(self):
        return {
            "asset_symbol": "SAMPLE",
            "asset_type": "stock",
            "timeframe": "5m",
            "pattern_id": "bull_flag_breakout",
            "pattern_quality_score": 82,
            "volume_confirmation_score": 84,
            "breakout_confirmation_score": 80,
            "price": 8.0,
            "entry_price": 8.1,
            "stop_loss": 7.8,
            "target_price": 8.9,
            "float_shares": 4_000_000,
            "daily_volume": 18_000_000,
            "relative_volume": 8,
            "intraday_percent_change": 16,
            "spread_percent": 0.2,
            "bid_ask_depth": 250_000,
            "catalyst_detected": True,
            "catalyst_type": "earnings",
            "catalyst_quality_score": 82,
            "minutes_since_midnight": 9 * 60 + 40,
            "balance_sheet": {
                "cash_and_cash_equivalents": 10_000_000,
                "current_assets": 20_000_000,
                "current_liabilities": 8_000_000,
                "long_term_debt": 2_000_000,
                "shareholder_equity": 12_000_000,
            },
            "raw_payload": {"must": "drop"},
            "api_key": "secret-value",
        }

    def test_pattern_detect_endpoint_compact_and_safe(self):
        response = self.client.post(
            "/api/automation/pattern-detect",
            json={
                "dry_run": True,
                "items": [
                    {
                        "asset_symbol": "SAMPLE",
                        "asset_type": "stock",
                        "timeframe": "5m",
                        "opening_range_high": 10,
                        "candles": [
                            {"open": 9.7, "high": 9.9, "low": 9.4, "close": 9.6, "volume": 1000},
                            {"open": 9.6, "high": 10.5, "low": 9.5, "close": 10.4, "volume": 4000},
                        ],
                    }
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertFalse(payload["auto_execution"])
        self.assertEqual(payload["actual_orders_submitted"], 0)
        self.assertEqual(payload["actual_bets_submitted"], 0)
        self.assertEqual(payload["actual_trades_submitted"], 0)
        self.assertTrue(payload["human_approval_required"])
        self.assertGreaterEqual(payload["detections_created"], 1)
        self.assertNotIn("'raw_payload':", str(payload))

    def test_small_account_review_endpoint_compact_and_safe(self):
        response = self.client.post(
            "/api/automation/small-account-review",
            json={"dry_run": True, "persist_queue": False, "items": [self._review_item()]},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "review_candidates_created")
        self.assertFalse(payload["provider_write"])
        self.assertFalse(payload["execution_allowed"])
        self.assertFalse(payload["live_execution_enabled"])
        self.assertFalse(payload["auto_execution"])
        self.assertEqual(payload["actual_orders_submitted"], 0)
        self.assertEqual(payload["actual_bets_submitted"], 0)
        self.assertEqual(payload["actual_trades_submitted"], 0)
        self.assertTrue(payload["human_approval_required"])
        self.assertEqual(payload["items_scanned"], 1)
        self.assertGreaterEqual(payload["review_queue_count"], 1)
        self.assertIn("sample_items", payload)
        self.assertTrue(payload["local_analyst_review"]["must_not_execute"])
        self.assertFalse(payload["local_analyst_review"]["external_model_called"])
        self.assertNotIn("secret-value", str(payload))
        self.assertNotIn("'raw_payload':", str(payload))
        self.assertNotIn("drop", str(payload))
        forbidden_actions = {"BUY", "SELL", "ORDER", "PLACE_ORDER", "EXECUTE_TRADE"}
        statuses = {str(item.get("queue_status", "")).upper() for item in payload.get("sample_items", [])}
        analyst_action = str(payload["local_analyst_review"].get("recommended_action", "")).upper()
        self.assertTrue(statuses.isdisjoint(forbidden_actions))
        self.assertNotIn(analyst_action, forbidden_actions)

    def test_small_account_review_rejects_non_dry_run(self):
        response = self.client.post("/api/automation/small-account-review", json={"dry_run": False, "items": []})
        self.assertEqual(response.status_code, 400)

    def test_new_get_endpoints_are_compact_and_safe(self):
        for path in (
            "/api/automation/pattern-review-queue",
            "/api/automation/pattern-calibration",
            "/api/automation/micro-outcome-calibration",
            "/api/automation/broker-quality",
            "/api/automation/balance-sheet-risk/SAMPLE",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertFalse(payload["provider_write"])
                self.assertFalse(payload["execution_allowed"])
                self.assertFalse(payload["live_execution_enabled"])
                self.assertFalse(payload["auto_execution"])
                self.assertEqual(payload["actual_orders_submitted"], 0)
                self.assertEqual(payload["actual_bets_submitted"], 0)
                self.assertEqual(payload["actual_trades_submitted"], 0)
                self.assertTrue(payload["human_approval_required"])
                self.assertNotIn("'raw_payload':", str(payload))


if __name__ == "__main__":
    unittest.main()
