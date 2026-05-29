import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from automation_scheduler.sharp_sportsbook_adapter import SharpSportsbookAdapter
from automation_scheduler.sportsbook_odds_provider import summarize_sportsbook_snapshot


class _MockResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _MockClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def get(self, url, headers=None, params=None):
        now_iso = datetime.now(timezone.utc).isoformat()
        self.calls.append(("GET", url, headers, params))
        return _MockResponse(
            200,
            {
                "data": [
                    {
                        "event_id": "evt1",
                        "sport": "basketball",
                        "league": "NBA",
                        "event_name": "A vs B",
                        "start_time": "2026-05-28T00:00:00+00:00",
                        "book": "sharp",
                        "market": "moneyline",
                        "selection": "A",
                        "line": None,
                        "odds": -110,
                        "timestamp": now_iso,
                        "api_key": "should_redact",
                    }
                ]
            },
        )


class TestSharpSportsbookAdapter(unittest.TestCase):
    def setUp(self):
        self.contract = {
            "provider_id": "sharp_sportsbook",
            "provider_type": "sportsbook_odds",
            "enabled": False,
            "dry_run": True,
            "live_calls_enabled": False,
            "required_credentials": ["SHARP_API_KEY"],
        }
        os.environ.pop("SHARP_API_KEY", None)
        os.environ.pop("SHARP_LIVE_READS_ENABLED", None)
        os.environ.pop("SHARP_PROVIDER_ENABLED", None)

    def test_defaults_disabled(self):
        adapter = SharpSportsbookAdapter(self.contract)
        cfg = adapter.validate_config()
        self.assertIn("provider_disabled", cfg["blockers"])
        self.assertIn("live_reads_disabled", cfg["blockers"])
        self.assertIn("blocked_missing_credentials", cfg["blockers"])
        self.assertFalse(cfg["provider_enabled"])
        self.assertFalse(cfg["live_calls_enabled"])

    def test_missing_live_reads_defaults_disabled(self):
        os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = False
        adapter = SharpSportsbookAdapter(contract)
        cfg = adapter.validate_config()
        self.assertIn("live_reads_disabled", cfg["blockers"])

    def test_both_flags_required_for_read_only_ready(self):
        os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = True
        adapter = SharpSportsbookAdapter(contract)
        cfg = adapter.validate_config()
        self.assertTrue(cfg["ok"])
        self.assertEqual(cfg["status"], "read_only_ready")
        self.assertEqual(cfg["blockers"], [])

    @patch("automation_scheduler.sharp_sportsbook_adapter.httpx.Client", new=_MockClient)
    def test_live_get_only_path(self):
        os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["dry_run"] = False
        contract["live_calls_enabled"] = True

        adapter = SharpSportsbookAdapter(contract)
        result = adapter.fetch_snapshot()
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["provider_enabled"])
        self.assertTrue(result["live_calls_enabled"])
        self.assertEqual(result["records_received"], 1)
        self.assertEqual(result["records_valid"], 1)
        self.assertEqual(result["records_rejected"], 0)
        rec = result["records"][0]
        self.assertAlmostEqual(rec["implied_probability"], 0.52380952, places=6)
        self.assertEqual(rec["decimal_odds"], 1.909091)
        self.assertEqual(rec["source_payload_redacted"]["api_key"], "[redacted]")

    def test_missing_credentials_do_not_crash(self):
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        adapter = SharpSportsbookAdapter(contract)
        snap = adapter.fetch_snapshot()
        self.assertEqual(snap["status"], "blocked_missing_credentials")
        self.assertEqual(snap["records"], [])

    def test_health_summary_compact_no_secret_leak(self):
        os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = True
        adapter = SharpSportsbookAdapter(contract)
        summary = summarize_sportsbook_snapshot(adapter.health_check())
        self.assertTrue(summary["provider_enabled"])
        self.assertTrue(summary["live_calls_enabled"])
        self.assertEqual(summary["credential_status"], "ok")
        self.assertNotIn("sharp_key_1234567890", str(summary))

    def test_malformed_payload_rejected(self):
        adapter = SharpSportsbookAdapter(self.contract)
        normalized = adapter.normalize_payload(
            {"event_id": "evt1", "market": "moneyline", "selection": "A", "odds": "bad", "timestamp": "2026-05-28T00:00:00+00:00"}
        )
        verdict = adapter.validate_payload(normalized)
        self.assertFalse(verdict["ok"])
        self.assertIn("malformed_odds", verdict["errors"])


if __name__ == "__main__":
    unittest.main()
