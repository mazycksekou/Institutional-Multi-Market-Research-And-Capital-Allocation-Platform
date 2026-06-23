from __future__ import annotations

import importlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.connectors.errors import ConnectorDisabledError
from src.connectors.prediction_market_data import (
    build_prediction_market_auth_requirement,
    build_prediction_market_connector_configuration,
    build_prediction_market_disabled_live_client,
    describe_prediction_market_connector_readiness,
)
from src.providers.prediction_markets import (
    PredictionMarketProviderAdapter,
    normalize_prediction_market_quote,
    normalize_prediction_market_snapshot,
    validate_prediction_market_payload,
)


class TestKalshiReadonlyAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = importlib.import_module("src.services.prediction_market_runtime_bridge")
        self.connector = importlib.import_module("src.connectors.prediction_market_data")
        self.provider = importlib.import_module("src.providers.prediction_markets")
        self.adapter = self.bridge.KalshiReadonlyAdapter({"enabled": False, "dry_run": True, "live_calls_enabled": False})

    def test_bridge_aliases_and_disabled_contract_are_local_only(self) -> None:
        self.assertIs(self.bridge.KalshiReadonlyAdapter, self.bridge.PredictionMarketReadonlyAdapter)
        cfg = self.adapter.validate_config()
        self.assertEqual(cfg["status"], "provider_disabled")
        self.assertIn("provider_disabled", cfg["blockers"])
        self.assertIn("live_reads_disabled", cfg["blockers"])
        self.assertIn("blocked_missing_credentials", cfg["blockers"])
        self.assertFalse(cfg["provider_enabled"])
        self.assertFalse(cfg["live_calls_enabled"])

        health = self.adapter.health_check()
        self.assertEqual(health["status"], "provider_disabled")
        self.assertFalse(health["provider_enabled"])
        self.assertFalse(health["live_calls_enabled"])
        self.assertTrue(health["dry_run"])

        url_diag = self.adapter.build_kalshi_url("markets_path")
        self.assertEqual(url_diag["provider_id"], "kalshi_prediction_market")
        self.assertFalse(url_diag["live_access_enabled"])
        self.assertIn("provider_disabled", url_diag["blockers"])

        for method_name in ("fetch_markets", "fetch_events", "fetch_snapshot"):
            with self.subTest(method_name=method_name):
                with self.assertRaises(ConnectorDisabledError):
                    getattr(self.adapter, method_name)()

        disabled_snapshot = self.bridge.get_kalshi_snapshot(self.adapter)
        self.assertTrue(disabled_snapshot["ok"])
        self.assertTrue(disabled_snapshot["dry_run"])
        self.assertEqual(disabled_snapshot["provider_id"], "kalshi_prediction_market")
        self.assertEqual(disabled_snapshot["status"], "provider_disabled")
        self.assertEqual(disabled_snapshot["records"], [])

    def test_connector_scaffolds_are_inert_and_no_live_client_methods_exist(self) -> None:
        configuration = build_prediction_market_connector_configuration(metadata={"bridge_module": "test"})
        auth = build_prediction_market_auth_requirement()
        readiness = describe_prediction_market_connector_readiness()
        disabled_client = build_prediction_market_disabled_live_client()

        self.assertEqual(configuration.provider, "prediction_market_data")
        self.assertTrue(configuration.read_only)
        self.assertFalse(configuration.live_access_enabled)
        self.assertEqual(auth.credential_names, ("PREDICTION_MARKET_API_KEY", "PREDICTION_MARKET_PRIVATE_KEY"))
        self.assertFalse(auth.live_access_enabled)
        self.assertEqual(readiness["provider"], "prediction_market_data")
        self.assertEqual(readiness["status"], "disabled")
        self.assertTrue(readiness["read_only"])
        self.assertFalse(readiness["live_access_enabled"])
        self.assertEqual(disabled_client.describe()["provider"], "prediction_market_data")

        for method_name in ("request", "fetch_markets", "fetch_events", "fetch_snapshot", "sign_request"):
            with self.subTest(method_name=method_name):
                with self.assertRaises(ConnectorDisabledError):
                    getattr(disabled_client, method_name)()

        connector_client = self.connector.build_prediction_market_read_only_client()
        self.assertEqual(connector_client.describe()["provider"], "prediction_market_data")
        with self.assertRaises(ConnectorDisabledError):
            connector_client.fetch_snapshot()

        self.assertTrue(self.connector.PredictionMarketConnectorClient is self.connector.PredictionMarketReadOnlyClient)

    def test_provider_adapter_normalizes_prediction_market_payloads_locally(self) -> None:
        provider_adapter = PredictionMarketProviderAdapter()
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "market_id": "KXTEST",
            "event_id": "KX-EVT",
            "contract_id": "KX-CONTRACT",
            "ticker": "KXTEST",
            "event_ticker": "KX-EVT",
            "title": "Prediction Market Demo",
            "yes_bid": 48,
            "yes_ask": 52,
            "no_bid": 47,
            "no_ask": 53,
            "liquidity": 1000,
            "volume": 250,
            "close_time": "2026-06-01T00:00:00+00:00",
            "timestamp": now_iso,
        }

        normalized_quote = normalize_prediction_market_quote(payload, provider="prediction_market", market_type="prediction_market")
        normalized_snapshot = normalize_prediction_market_snapshot(payload, provider="prediction_market", market_type="prediction_market")
        validated = validate_prediction_market_payload(normalized_quote)
        adapter_quote = provider_adapter.normalize_payload(payload)

        self.assertEqual(normalized_quote["provider_type"], "prediction_market")
        self.assertEqual(normalized_snapshot["provider_type"], "prediction_market")
        self.assertAlmostEqual(normalized_quote["yes_bid"], 0.48)
        self.assertAlmostEqual(normalized_quote["yes_ask"], 0.52)
        self.assertAlmostEqual(normalized_quote["mid_probability"], 0.5)
        self.assertTrue(validated["ok"])
        self.assertEqual(adapter_quote["provider_type"], "prediction_market")
        adapter_health = provider_adapter.health_check()
        self.assertEqual(adapter_health["status"], "scaffold_only")
        self.assertIn("read_only_category_adapter", adapter_health["blockers"])

    def test_snapshot_helpers_write_and_round_trip_without_leaking_secrets(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "ok": True,
            "status": "provider_disabled",
            "provider_id": "kalshi_prediction_market",
            "provider_name": "Kalshi Prediction Market",
            "dry_run": True,
            "records_received": 1,
            "records_valid": 1,
            "records_rejected": 0,
            "records": [
                {
                    "market_id": "KX-1",
                    "event_id": "KX-EVT-1",
                    "ticker": "KX-1",
                    "contract_id": "KX-1",
                    "yes_price": 0.48,
                    "no_price": 0.52,
                    "timestamp": now_iso,
                    "source_payload_redacted": {"api_key": "[redacted]", "api_secret": "[redacted]"},
                }
            ],
        }

        normalized = self.bridge.normalize_prediction_market_snapshot(snapshot)
        verdict = self.bridge.validate_prediction_market_snapshot(snapshot)
        summary = self.bridge.summarize_prediction_market_snapshot(snapshot)

        self.assertEqual(normalized["provider_id"], "kalshi_prediction_market")
        self.assertEqual(verdict["status"], "accepted")
        self.assertEqual(summary["status"], "provider_disabled")
        self.assertEqual(summary["records_valid"], 1)

        with tempfile.TemporaryDirectory() as tmp:
            path = self.bridge.write_prediction_market_snapshot(snapshot, base_data_dir=tmp)
            text = Path(path).read_text(encoding="utf-8")
            self.assertIn("[redacted]", text)
            self.assertNotIn("api_key\": \"live", text)
            self.assertNotIn("api_secret\": \"live", text)


if __name__ == "__main__":
    unittest.main()
