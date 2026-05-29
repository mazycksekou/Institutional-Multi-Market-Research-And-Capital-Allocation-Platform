import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import httpx

from automation_scheduler.kalshi_readonly_adapter import KalshiReadonlyAdapter


class _MockResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _MockClient:
    response_status = 200
    markets_payload = {"markets": []}
    events_payload = {"events": []}
    should_timeout = False
    calls = []

    def __init__(self, *args, **kwargs):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def get(self, url, headers=None, params=None):
        if self.should_timeout:
            raise httpx.TimeoutException("timeout")
        _MockClient.calls.append(("GET", url, headers or {}, params or {}))
        if "events" in url:
            return _MockResponse(self.response_status, self.events_payload)
        return _MockResponse(self.response_status, self.markets_payload)

    def post(self, *args, **kwargs):
        _MockClient.calls.append(("POST", args, kwargs))
        return _MockResponse(405, {"error": "not_allowed"})

    def put(self, *args, **kwargs):
        _MockClient.calls.append(("PUT", args, kwargs))
        return _MockResponse(405, {"error": "not_allowed"})

    def patch(self, *args, **kwargs):
        _MockClient.calls.append(("PATCH", args, kwargs))
        return _MockResponse(405, {"error": "not_allowed"})

    def delete(self, *args, **kwargs):
        _MockClient.calls.append(("DELETE", args, kwargs))
        return _MockResponse(405, {"error": "not_allowed"})


class TestKalshiReadonlyAdapter(unittest.TestCase):
    def setUp(self):
        for key in (
            "KALSHI_PROVIDER_ENABLED",
            "KALSHI_LIVE_READS_ENABLED",
            "KALSHI_API_BASE_URL",
            "KALSHI_API_KEY",
            "KALSHI_API_SECRET",
            "KALSHI_API_TIMEOUT_SECONDS",
            "KALSHI_MARKETS_PATH",
            "KALSHI_EVENTS_PATH",
        ):
            os.environ.pop(key, None)
        self.contract = {
            "provider_id": "kalshi_prediction_market",
            "provider_type": "prediction_market",
            "enabled": False,
            "dry_run": True,
            "live_calls_enabled": False,
            "required_credentials": ["KALSHI_API_KEY", "KALSHI_API_SECRET"],
            "auto_execution_enabled": False,
            "kalshi_order_execution_enabled": False,
        }
        _MockClient.response_status = 200
        _MockClient.markets_payload = {"markets": []}
        _MockClient.events_payload = {"events": []}
        _MockClient.should_timeout = False
        _MockClient.calls = []

    def test_defaults_disabled(self):
        adapter = KalshiReadonlyAdapter(self.contract)
        cfg = adapter.validate_config()
        self.assertIn("provider_disabled", cfg["blockers"])
        self.assertIn("live_reads_disabled", cfg["blockers"])
        self.assertIn("blocked_missing_credentials", cfg["blockers"])
        self.assertFalse(cfg["provider_enabled"])
        self.assertFalse(cfg["live_calls_enabled"])

    def test_missing_credentials_produces_blocked_missing_credentials(self):
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        adapter = KalshiReadonlyAdapter(contract)
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["status"], "blocked_missing_credentials")
        self.assertEqual(snapshot["records"], [])

    @patch("automation_scheduler.kalshi_readonly_adapter.httpx.Client", new=_MockClient)
    def test_live_reads_disabled_does_not_call_external_network(self):
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = False
        adapter = KalshiReadonlyAdapter(contract)
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["status"], "live_reads_disabled")
        self.assertEqual(_MockClient.calls, [])

    @patch("automation_scheduler.kalshi_readonly_adapter.httpx.Client", new=_MockClient)
    def test_live_get_only_path_normalizes_prediction_market_fields(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = "kalshi_secret_1234567890"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = True
        _MockClient.events_payload = {
            "events": [
                {
                    "event_ticker": "EVT-1",
                    "title": "Fed funds event",
                    "close_time": "2026-06-01T00:00:00+00:00",
                    "updated_at": now_iso,
                }
            ]
        }
        _MockClient.markets_payload = {
            "markets": [
                {
                    "market_id": "MKT-1",
                    "event_ticker": "EVT-1",
                    "contract_id": "CTR-1",
                    "contract_title": "Rate above threshold",
                    "ticker": "FED-ABOVE",
                    "yes_bid": 47,
                    "yes_ask": 49,
                    "volume": 2500,
                    "open_interest": 1200,
                    "close_time": "2026-06-01T00:00:00+00:00",
                    "settlement_rule": "Resolved by official release",
                    "timestamp": now_iso,
                    "api_key": "must_redact",
                }
            ]
        }
        adapter = KalshiReadonlyAdapter(contract)
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["status"], "live_snapshot_complete")
        self.assertEqual(snapshot["records_received"], 1)
        self.assertEqual(snapshot["records_valid"], 1)
        self.assertEqual(snapshot["records_rejected"], 0)
        row = snapshot["records"][0]
        self.assertAlmostEqual(row["yes_price"], 0.48, places=6)
        self.assertAlmostEqual(row["implied_probability"], 0.48, places=6)
        self.assertAlmostEqual(row["no_price"], 0.52, places=6)
        self.assertEqual(row["volume"], 2500.0)
        self.assertEqual(row["open_interest"], 1200.0)
        self.assertEqual(row["close_time"], "2026-06-01T00:00:00+00:00")
        self.assertEqual(row["timestamp"], now_iso)
        self.assertEqual(row["settlement_rule"], "Resolved by official release")
        self.assertIn("source_payload_redacted", row)
        self.assertNotIn("kalshi_key_1234567890", str(snapshot))
        self.assertNotIn("kalshi_secret_1234567890", str(snapshot))
        methods = [call[0] for call in _MockClient.calls]
        self.assertTrue(all(method == "GET" for method in methods))
        self.assertNotIn("POST", methods)
        self.assertNotIn("PUT", methods)
        self.assertNotIn("PATCH", methods)
        self.assertNotIn("DELETE", methods)

    @patch("automation_scheduler.kalshi_readonly_adapter.httpx.Client", new=_MockClient)
    def test_malformed_prices_are_rejected(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = "kalshi_secret_1234567890"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = True
        _MockClient.events_payload = {"events": [{"event_ticker": "EVT-1", "title": "Event 1"}]}
        _MockClient.markets_payload = {
            "markets": [
                {
                    "market_id": "MKT-1",
                    "event_ticker": "EVT-1",
                    "contract_id": "CTR-1",
                    "contract_title": "Bad price",
                    "yes_price": "not_a_number",
                    "timestamp": now_iso,
                }
            ]
        }
        adapter = KalshiReadonlyAdapter(contract)
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["records_valid"], 0)
        self.assertGreaterEqual(snapshot["records_rejected"], 1)
        self.assertIn("malformed_price", snapshot["rejection_reason_counts"])

    def test_build_kalshi_url_diagnostic_redacted(self):
        os.environ["KALSHI_API_BASE_URL"] = "https://api.kalshi.com/trade-api/v2/"
        os.environ["KALSHI_MARKETS_PATH"] = "/markets"
        adapter = KalshiReadonlyAdapter(self.contract)
        diag = adapter.build_kalshi_url("markets_path")
        self.assertEqual(diag["url_host"], "api.kalshi.com")
        self.assertTrue(diag["secret_redacted"])
        self.assertTrue(diag["query_redacted"])
        self.assertNotIn("authorization", str(diag).lower())


if __name__ == "__main__":
    unittest.main()
