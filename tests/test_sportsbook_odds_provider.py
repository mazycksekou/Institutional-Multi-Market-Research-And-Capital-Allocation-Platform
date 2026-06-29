import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.services.streamlit_dashboard_facade import compact_provider_status
from src.services.streamlit_dashboard_facade import run_scheduler_once
from src.connectors.odds_data import build_odds_data_connector_configuration, describe_odds_data_connector_readiness
from src.providers.registry import get_provider_registry
from src.providers.sportsbooks.contracts import validate_sportsbook_payload
from src.services.odds_runtime_bridge import (
    SharpSportsbookAdapter,
    normalize_sportsbook_snapshot,
    summarize_sportsbook_snapshot,
    write_sportsbook_snapshot,
)


class TestSportsbookOddsProvider(unittest.TestCase):
    def setUp(self):
        os.environ["LEGACY_PROVIDER_REGISTRY_COMPAT"] = "true"
        os.environ.pop("SHARP_API_KEY", None)
        os.environ.pop("SHARP_LIVE_READS_ENABLED", None)
        os.environ.pop("SHARP_PROVIDER_ENABLED", None)

    def tearDown(self):
        os.environ.pop("LEGACY_PROVIDER_REGISTRY_COMPAT", None)

    def test_registry_contains_sharp_metadata(self):
        registry = get_provider_registry()
        sharp = registry["sharp_sportsbook"]
        self.assertEqual(sharp["provider_type"], "sportsbook_odds")
        self.assertFalse(sharp["enabled"])
        self.assertFalse(sharp["live_calls_enabled"])
        self.assertTrue(sharp["supports_polling"])
        self.assertFalse(sharp["supports_streaming"])
        self.assertEqual(sharp["required_credentials"], ["SHARP_API_KEY"])
        self.assertEqual(build_odds_data_connector_configuration().provider, "odds_data")
        self.assertEqual(describe_odds_data_connector_readiness()["status"], "disabled")

    def test_dry_run_placeholder_snapshot(self):
        adapter = SharpSportsbookAdapter(get_provider_registry()["sharp_sportsbook"])
        snap = adapter.fetch_snapshot()
        self.assertIn(snap["status"], {"provider_disabled", "live_reads_disabled", "blocked_missing_credentials"})
        normalized = normalize_sportsbook_snapshot(snap)
        summary = summarize_sportsbook_snapshot(normalized)
        compact = compact_provider_status(summary)
        self.assertIn(compact["status"], {"provider_disabled", "live_reads_disabled", "blocked_missing_credentials"})
        self.assertNotIn("source_payload_redacted", str(compact))

    def test_compact_provider_error_includes_safe_diagnostic(self):
        snapshot = {
            "ok": True,
            "status": "provider_error",
            "provider_id": "sharp_sportsbook",
            "provider_enabled": True,
            "live_calls_enabled": True,
            "credential_status": "ok",
            "rejection_reason_counts": {"malformed_odds": 3},
            "http_status": 404,
            "diagnostic": {
                "url_host": "api.sharp.app",
                "url_path": "/v1/odds",
                "method": "GET",
                "secret_redacted": True,
                "authorization": "Bearer secret",
                "raw_body": {"error": "not found"},
            },
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "blockers": ["http_404"],
        }
        summary = summarize_sportsbook_snapshot(snapshot)
        compact = compact_provider_status(summary)
        self.assertEqual(compact["status"], "provider_error")
        self.assertEqual(compact["http_status"], 404)
        self.assertEqual(compact["diagnostic"]["url_host"], "api.sharp.app")
        self.assertEqual(compact["diagnostic"]["url_path"], "/v1/odds")
        self.assertEqual(compact["diagnostic"]["method"], "GET")
        self.assertTrue(compact["diagnostic"]["secret_redacted"])
        self.assertEqual(compact["rejection_reason_counts"]["malformed_odds"], 3)
        self.assertNotIn("authorization", str(compact).lower())
        self.assertNotIn("raw_body", str(compact).lower())

    def test_validate_snapshot_stale_payload_flagged(self):
        stale = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        verdict = validate_sportsbook_payload(
            {
                "event_id": "evt1",
                "market": "moneyline",
                "selection": "A",
                "odds": -110,
                "timestamp": stale,
            }
        )
        self.assertFalse(verdict["ok"])
        self.assertIn("stale_timestamp", verdict["errors"])

    def test_write_snapshot_redacts_secrets(self):
        snapshot = {
            "ok": True,
            "status": "ok",
            "provider_id": "sharp_sportsbook",
            "dry_run": False,
            "records": [
                {
                    "event_id": "evt1",
                    "market": "moneyline",
                    "selection": "A",
                    "odds": -110,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source_payload_redacted": {"api_key": "[redacted]"},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = write_sportsbook_snapshot(snapshot, base_data_dir=tmp)
            self.assertTrue(path.endswith("sharp_sportsbook_snapshot.json"))
            saved = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertNotIn("sharp_key", str(saved))

    def test_scheduler_skips_when_disabled_or_live_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = run_scheduler_once(base_data_dir=tmp, dry_run=True)
            reasons = [item["reason"] for item in run["skipped_items"] if item.get("provider_id") == "sharp_sportsbook"]
            self.assertTrue(reasons)
            self.assertIn(reasons[0], {"provider_disabled", "live_reads_disabled", "missing_credentials", "dry_run_placeholder"})

    def test_read_only_get_only_no_write_methods(self):
        source = Path("src/services/odds_runtime_bridge.py").read_text(encoding="utf-8").lower()
        self.assertNotIn(".post(", source)
        self.assertNotIn(".put(", source)
        self.assertNotIn(".patch(", source)
        self.assertNotIn(".delete(", source)


if __name__ == "__main__":
    unittest.main()
