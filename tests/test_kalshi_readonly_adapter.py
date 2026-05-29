import base64
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

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
    raise_exception = None
    calls = []

    def __init__(self, *args, **kwargs):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def get(self, url, headers=None, params=None):
        if self.raise_exception is not None:
            raise self.raise_exception
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


_TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_TEST_PRIVATE_KEY_PEM = _TEST_PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode("utf-8")


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
        _MockClient.raise_exception = None
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
        os.environ["KALSHI_API_SECRET"] = _TEST_PRIVATE_KEY_PEM
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
        self.assertNotIn("BEGIN PRIVATE KEY", str(snapshot))
        methods = [call[0] for call in _MockClient.calls]
        self.assertTrue(all(method == "GET" for method in methods))
        self.assertNotIn("POST", methods)
        self.assertNotIn("PUT", methods)
        self.assertNotIn("PATCH", methods)
        self.assertNotIn("DELETE", methods)
        _, _, sent_headers, sent_params = _MockClient.calls[0]
        self.assertIn("KALSHI-ACCESS-KEY", sent_headers)
        self.assertIn("KALSHI-ACCESS-TIMESTAMP", sent_headers)
        self.assertIn("KALSHI-ACCESS-SIGNATURE", sent_headers)
        self.assertNotIn("KALSHI-ACCESS-SECRET", sent_headers)
        self.assertIsInstance(sent_params, dict)

    @patch("automation_scheduler.kalshi_readonly_adapter.httpx.Client", new=_MockClient)
    def test_live_normalizes_dollars_based_price_fields(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = _TEST_PRIVATE_KEY_PEM
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = True
        _MockClient.events_payload = {"events": [{"event_ticker": "EVT-1", "title": "Event 1", "updated_at": now_iso}]}
        _MockClient.markets_payload = {
            "markets": [
                {
                    "event_ticker": "EVT-1",
                    "ticker": "KX-1",
                    "yes_bid_dollars": 0.44,
                    "yes_ask_dollars": 0.46,
                    "no_bid_dollars": 0.54,
                    "no_ask_dollars": 0.56,
                    "last_price_dollars": 0.45,
                    "volume_fp": 1200,
                    "open_interest_fp": 900,
                    "rules_primary": "official_result",
                    "close_time": "2026-06-01T00:00:00+00:00",
                    "updated_time": now_iso,
                }
            ]
        }
        adapter = KalshiReadonlyAdapter(contract)
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["records_valid"], 1)
        row = snapshot["records"][0]
        self.assertAlmostEqual(row["yes_bid"], 0.44, places=6)
        self.assertAlmostEqual(row["yes_ask"], 0.46, places=6)
        self.assertAlmostEqual(row["yes_price"], 0.45, places=6)
        self.assertEqual(row["volume"], 1200.0)
        self.assertEqual(row["open_interest"], 900.0)
        self.assertEqual(row["settlement_rule"], "official_result")
        self.assertEqual(row["timestamp"], now_iso)

    @patch("automation_scheduler.kalshi_readonly_adapter.httpx.Client", new=_MockClient)
    def test_malformed_prices_are_rejected(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = _TEST_PRIVATE_KEY_PEM
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
        os.environ["KALSHI_API_BASE_URL"] = "https://external-api.kalshi.com/trade-api/v2/"
        os.environ["KALSHI_MARKETS_PATH"] = "/markets"
        adapter = KalshiReadonlyAdapter(self.contract)
        diag = adapter.build_kalshi_url("markets_path")
        self.assertEqual(diag["url_host"], "external-api.kalshi.com")
        self.assertTrue(diag["secret_redacted"])
        self.assertTrue(diag["query_redacted"])
        self.assertNotIn("authorization", str(diag).lower())

    def test_default_base_url_uses_documented_external_host(self):
        adapter = KalshiReadonlyAdapter(self.contract)
        diag = adapter.build_kalshi_url("markets_path")
        self.assertEqual(diag["url_host"], "external-api.kalshi.com")
        self.assertEqual(diag["url_path"], "/trade-api/v2/markets")

    def test_health_read_only_ready_with_credentials_and_flags(self):
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = _TEST_PRIVATE_KEY_PEM
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = True
        adapter = KalshiReadonlyAdapter(contract)
        health = adapter.health_check()
        self.assertEqual(health["status"], "read_only_ready")
        self.assertEqual(health["credential_status"], "ok")
        self.assertTrue(health["provider_enabled"])
        self.assertTrue(health["live_calls_enabled"])
        self.assertTrue(health["dry_run"])
        self.assertNotIn("order", str(health).lower())
        self.assertNotIn("trade", str(health).lower())
        self.assertNotIn("execution_enabled\": true", str(health).lower())

    @patch("automation_scheduler.kalshi_readonly_adapter.httpx.Client", new=_MockClient)
    def test_provider_unreachable_is_classified_and_redacted(self):
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = _TEST_PRIVATE_KEY_PEM
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = True
        _MockClient.raise_exception = httpx.ConnectError(
            "Name or service not known",
            request=httpx.Request("GET", "https://external-api.kalshi.com/trade-api/v2/markets"),
        )
        adapter = KalshiReadonlyAdapter(contract)
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["status"], "provider_error")
        self.assertIn("dns_error", snapshot["blockers"])
        self.assertEqual(snapshot["http_status"], None)
        diag = snapshot.get("diagnostic") or {}
        self.assertEqual(diag.get("error_category"), "dns_error")
        self.assertEqual(diag.get("method"), "GET")
        self.assertTrue(diag.get("secret_redacted"))
        self.assertIn("url_host", diag)
        self.assertIn("url_path", diag)
        self.assertIn("timeout_seconds", diag)
        self.assertIn("retry_count", diag)
        self.assertNotIn("kalshi_key_1234567890", str(snapshot))
        self.assertNotIn("BEGIN PRIVATE KEY", str(snapshot))

    def test_signature_payload_uses_timestamp_method_and_path_only(self):
        adapter = KalshiReadonlyAdapter(self.contract)
        payload = adapter._build_signature_payload(
            method="GET",
            url="https://external-api.kalshi.com/trade-api/v2/markets?limit=10",
            timestamp_ms="1710000000000",
        )
        self.assertEqual(payload, b"1710000000000GET/trade-api/v2/markets")

    def test_built_headers_are_http_safe_and_verifiable(self):
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = _TEST_PRIVATE_KEY_PEM.replace("\n", "\\n")
        adapter = KalshiReadonlyAdapter(self.contract)
        headers = adapter._build_headers(method="GET", url="https://external-api.kalshi.com/trade-api/v2/markets")
        self.assertNotIn("KALSHI-ACCESS-SECRET", headers)
        for value in headers.values():
            self.assertIsInstance(value, str)
            self.assertNotIn("\n", value)
            self.assertNotIn("\r", value)
        timestamp = headers["KALSHI-ACCESS-TIMESTAMP"]
        signature = headers["KALSHI-ACCESS-SIGNATURE"]
        payload = adapter._build_signature_payload(
            method="GET",
            url="https://external-api.kalshi.com/trade-api/v2/markets",
            timestamp_ms=timestamp,
        )
        _TEST_PRIVATE_KEY.public_key().verify(
            base64.b64decode(signature),
            payload,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256(),
        )

    @patch("automation_scheduler.kalshi_readonly_adapter.httpx.Client", new=_MockClient)
    def test_malformed_credential_shape_returns_blocked_invalid_credentials(self):
        os.environ["KALSHI_PROVIDER_ENABLED"] = "true"
        os.environ["KALSHI_LIVE_READS_ENABLED"] = "true"
        os.environ["KALSHI_API_KEY"] = "kalshi_key_1234567890"
        os.environ["KALSHI_API_SECRET"] = "not_a_private_key"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        snapshot = KalshiReadonlyAdapter(contract).fetch_snapshot()
        self.assertEqual(snapshot["status"], "provider_error")
        self.assertIn("blocked_invalid_credentials", snapshot["blockers"])
        self.assertEqual(snapshot.get("http_status"), None)
        self.assertEqual(snapshot.get("diagnostic", {}).get("error_category"), "request_build_error")
        self.assertNotIn("not_a_private_key", str(snapshot))


if __name__ == "__main__":
    unittest.main()
