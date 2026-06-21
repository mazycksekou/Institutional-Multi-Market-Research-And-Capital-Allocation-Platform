import os
import re
import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from automation_scheduler.kalshi_market_provider import (
    normalize_kalshi_snapshot,
    summarize_kalshi_snapshot,
    validate_kalshi_snapshot,
    write_kalshi_snapshot,
)
from src.providers.registry import get_provider_registry
from automation_scheduler.response_compactor import compact_provider_status
from automation_scheduler.scheduler_runner import run_scheduler_once


class TestKalshiMarketProvider(unittest.TestCase):
    def setUp(self):
        os.environ["LEGACY_PROVIDER_REGISTRY_COMPAT"] = "true"
        for key in (
            "KALSHI_PROVIDER_ENABLED",
            "KALSHI_LIVE_READS_ENABLED",
            "KALSHI_API_KEY",
            "KALSHI_API_SECRET",
        ):
            os.environ.pop(key, None)

    def tearDown(self):
        os.environ.pop("LEGACY_PROVIDER_REGISTRY_COMPAT", None)

    def test_normalize_validate_and_summarize_snapshot(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": "kalshi_prediction_market",
            "provider_enabled": True,
            "live_calls_enabled": True,
            "credential_status": "ok",
            "dry_run": False,
            "records_received": 1,
            "records_valid": 1,
            "records_rejected": 0,
            "records": [
                {
                    "provider_id": "kalshi_prediction_market",
                    "provider_name": "Kalshi Prediction Market",
                    "received_at": now_iso,
                    "market_id": "MKT-1",
                    "event_id": "EVT-1",
                    "event_title": "Macro Event",
                    "contract_id": "CTR-1",
                    "contract_title": "Outcome A",
                    "ticker": "MKT-1",
                    "yes_bid": 0.47,
                    "yes_ask": 0.49,
                    "no_bid": 0.51,
                    "no_ask": 0.53,
                    "yes_price": 0.48,
                    "no_price": 0.52,
                    "implied_probability": 0.48,
                    "volume": 2500.0,
                    "open_interest": 1200.0,
                    "liquidity_score": 0.98,
                    "close_time": "2026-06-01T00:00:00+00:00",
                    "status": "open",
                    "settlement_rule": "Official publication",
                    "timestamp": now_iso,
                    "source_payload_redacted": {"authorization": "[redacted]"},
                    "schema_version": "automation_scheduler.v1.kalshi_prediction_market.v1",
                }
            ],
            "timestamp": now_iso,
        }
        normalized = normalize_kalshi_snapshot(snapshot)
        self.assertEqual(normalized["provider_id"], "kalshi_prediction_market")
        self.assertEqual(normalized["records_received"], 1)
        verdict = validate_kalshi_snapshot(snapshot)
        self.assertEqual(verdict["status"], "accepted")
        summary = summarize_kalshi_snapshot(snapshot)
        self.assertEqual(summary["records_valid"], 1)
        compact = compact_provider_status(summary)
        self.assertNotIn("source_payload_redacted", str(compact))
        self.assertNotIn("authorization", str(compact).lower())
        self.assertNotIn("auto_execution_enabled", compact)
        self.assertNotIn("order", str(compact).lower())
        self.assertNotIn("trade", str(compact).lower())

    def test_write_snapshot_and_secret_redaction(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "ok": True,
            "status": "live_snapshot_complete",
            "provider_id": "kalshi_prediction_market",
            "records_received": 1,
            "records_valid": 1,
            "records_rejected": 0,
            "records": [
                {
                    "market_id": "MKT-1",
                    "event_id": "EVT-1",
                    "contract_id": "CTR-1",
                    "yes_price": 0.55,
                    "no_price": 0.45,
                    "timestamp": now_iso,
                    "source_payload_redacted": {"api_key": "[redacted]", "api_secret": "[redacted]"},
                }
            ],
            "timestamp": now_iso,
        }
        with TemporaryDirectory() as tmp:
            path = write_kalshi_snapshot(snapshot, base_data_dir=tmp)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertNotIn("api_key\": \"live", text)
            self.assertNotIn("api_secret\": \"live", text)
            self.assertIn("[redacted]", text)

    def test_stale_payloads_are_flagged(self):
        stale_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        snapshot = {
            "records": [
                {
                    "market_id": "MKT-1",
                    "event_id": "EVT-1",
                    "contract_id": "CTR-1",
                    "yes_price": 0.55,
                    "no_price": 0.45,
                    "timestamp": stale_ts,
                }
            ]
        }
        verdict = validate_kalshi_snapshot(snapshot)
        self.assertEqual(verdict["status"], "rejected")
        self.assertIn("stale_timestamp", verdict["errors"])

    def test_provider_registry_includes_kalshi_metadata(self):
        registry = get_provider_registry()
        self.assertIn("kalshi_prediction_market", registry)
        item = registry["kalshi_prediction_market"]
        self.assertFalse(item["enabled"])
        self.assertFalse(item["live_calls_enabled"])
        self.assertEqual(item["provider_type"], "prediction_market")
        self.assertEqual(item["required_credentials"], ["KALSHI_API_KEY", "KALSHI_API_SECRET"])

    def test_scheduler_skips_kalshi_when_disabled_or_live_reads_disabled(self):
        with TemporaryDirectory() as tmp:
            result = run_scheduler_once(base_data_dir=tmp, dry_run=True, injected_data={"skipped_items": []})
            skipped = result.get("skipped_items", [])
            reasons = {row.get("provider_id"): row.get("reason") for row in skipped if isinstance(row, dict)}
            self.assertIn("kalshi_prediction_market", reasons)
            self.assertIn(reasons["kalshi_prediction_market"], {"provider_disabled", "live_reads_disabled", "missing_credentials", "dry_run_placeholder"})

    def test_banned_language_not_present(self):
        payload_text = str(
            summarize_kalshi_snapshot(
                {
                    "provider_id": "kalshi_prediction_market",
                    "status": "provider_disabled",
                    "records_received": 0,
                    "records_valid": 0,
                    "records_rejected": 0,
                }
            )
        ).lower()
        for banned_pattern in (r"\block\b", r"\bguaranteed\b", r"\brisk-free\b", r"\bsure thing\b", r"\bcan't lose\b"):
            self.assertIsNone(re.search(banned_pattern, payload_text))


if __name__ == "__main__":
    unittest.main()
