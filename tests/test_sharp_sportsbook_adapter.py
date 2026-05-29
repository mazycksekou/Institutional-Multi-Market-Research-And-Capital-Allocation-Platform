import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import httpx

from automation_scheduler.sharp_sportsbook_adapter import SharpSportsbookAdapter
from automation_scheduler.sportsbook_odds_provider import summarize_sportsbook_snapshot


class _MockResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _MockClient:
    response_status = 200
    response_payload = {"data": []}
    should_timeout = False
    last_call: tuple | None = None

    def __init__(self, *args, **kwargs):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def get(self, url, headers=None, params=None):
        if self.should_timeout:
            raise httpx.TimeoutException("timed out")
        now_iso = datetime.now(timezone.utc).isoformat()
        self.calls.append(("GET", url, headers, params))
        _MockClient.last_call = (url, headers or {}, params or {})
        payload = self.response_payload
        if payload == "__default__":
            payload = {
                "data": [
                    {
                        "eventId": "evt1",
                        "sportName": "basketball",
                        "leagueName": "NBA",
                        "homeTeam": "B",
                        "awayTeam": "A",
                        "startsAt": "2026-05-28T00:00:00+00:00",
                        "markets": [
                            {
                                "marketName": "moneyline",
                                "books": [
                                    {
                                        "name": "sharp",
                                        "outcomes": [
                                            {
                                                "name": "A",
                                                "americanOdds": -110,
                                                "updatedAt": now_iso,
                                                "api_key": "should_redact",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        return _MockResponse(self.response_status, payload)


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
        os.environ.pop("SHARP_API_BASE_URL", None)
        os.environ.pop("SHARP_EVENTS_PATH", None)
        os.environ.pop("SHARP_ODDS_PATH", None)
        os.environ.pop("SHARP_PLAYER_PROPS_PATH", None)
        os.environ.pop("SHARP_SPORTS_PATH", None)
        _MockClient.response_status = 200
        _MockClient.response_payload = "__default__"
        _MockClient.should_timeout = False
        _MockClient.last_call = None

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
        self.assertEqual(result["status"], "live_snapshot_complete")
        self.assertTrue(result["provider_enabled"])
        self.assertTrue(result["live_calls_enabled"])
        self.assertEqual(result["records_received"], 1)
        self.assertEqual(result["records_valid"], 1)
        self.assertEqual(result["records_rejected"], 0)
        rec = result["records"][0]
        self.assertAlmostEqual(rec["implied_probability"], 0.52380952, places=6)
        self.assertEqual(rec["decimal_odds"], 1.909091)
        self.assertIn("api_key", rec["source_payload_redacted"]["outcome_keys"])

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

    def test_decimal_odds_normalize_and_probability(self):
        adapter = SharpSportsbookAdapter(self.contract)
        normalized, warnings, reject = adapter._normalize_flattened_row(
            {
                "event": {
                    "eventId": "evt2",
                    "sportName": "soccer",
                    "leagueName": "EPL",
                    "name": "X vs Y",
                    "startsAt": "2026-05-28T00:00:00+00:00",
                },
                "market": {"marketName": "moneyline"},
                "book": {"name": "sharp"},
                "outcome": {"name": "X", "decimalOdds": 2.5, "updatedAt": "2026-05-28T00:00:00+00:00"},
            }
        )
        self.assertIsNone(reject)
        self.assertEqual(normalized["odds"], 2.5)
        self.assertEqual(normalized["decimal_odds"], 2.5)
        self.assertAlmostEqual(normalized["implied_probability"], 0.4, places=6)
        self.assertIn("odds_format_decimal", warnings)

    @patch("automation_scheduler.sharp_sportsbook_adapter.httpx.Client", new=_MockClient)
    def test_rejection_reason_counts_and_debug_summary(self):
        os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
        os.environ["SHARP_PROVIDER_ENABLED"] = "true"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = False
        _MockClient.response_payload = {
            "data": [
                {
                    "eventId": "evt_ok",
                    "sportName": "basketball",
                    "leagueName": "NBA",
                    "markets": [
                        {
                            "marketName": "moneyline",
                            "books": [{"name": "sharp", "outcomes": [{"name": "A", "americanOdds": -120}]}],
                        }
                    ],
                },
                {
                    "eventId": "evt_bad",
                    "markets": [{"marketName": "moneyline", "books": [{"name": "sharp", "outcomes": [{"name": "B"}]}]}],
                },
            ]
        }
        adapter = SharpSportsbookAdapter(contract)
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["records_received"], 2)
        self.assertEqual(snapshot["records_valid"], 1)
        self.assertEqual(snapshot["records_rejected"], 1)
        self.assertIn("malformed_odds", snapshot["rejection_reason_counts"])
        debug = snapshot["internal_debug_summary"]
        self.assertIn("top_level_keys_present", debug)
        self.assertIn("candidate_outcome_count", debug)
        self.assertTrue(debug["secret_redacted"])

    def test_build_sharp_url_diagnostic_redacted(self):
        os.environ["SHARP_API_BASE_URL"] = "https://api.sharp.app/"
        os.environ["SHARP_ODDS_PATH"] = "/v1/odds"
        adapter = SharpSportsbookAdapter(self.contract)
        diag = adapter.build_sharp_url("odds_path")
        self.assertTrue(diag["base_url_present"])
        self.assertEqual(diag["resolved_path"], "/v1/odds")
        self.assertEqual(diag["url_host"], "api.sharp.app")
        self.assertEqual(diag["url_path"], "/v1/odds")
        self.assertTrue(diag["query_redacted"])
        self.assertTrue(diag["secret_redacted"])
        self.assertNotIn("api_key", str(diag).lower())

    @patch("automation_scheduler.sharp_sportsbook_adapter.httpx.Client", new=_MockClient)
    def test_path_joining_handles_leading_and_double_slash(self):
        os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
        os.environ["SHARP_PROVIDER_ENABLED"] = "true"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        os.environ["SHARP_API_BASE_URL"] = "https://api.sharp.app///"
        os.environ["SHARP_ODDS_PATH"] = "/v1//odds"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = False
        adapter = SharpSportsbookAdapter(contract)
        _MockClient.response_payload = "__default__"
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["status"], "live_snapshot_complete")
        self.assertIsNotNone(_MockClient.last_call)
        called_url = _MockClient.last_call[0]
        self.assertEqual(called_url, "https://api.sharp.app/v1/odds")

    @patch("automation_scheduler.sharp_sportsbook_adapter.httpx.Client", new=_MockClient)
    def test_path_joining_handles_missing_leading_slash(self):
        os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
        os.environ["SHARP_PROVIDER_ENABLED"] = "true"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        os.environ["SHARP_API_BASE_URL"] = "https://api.sharp.app"
        os.environ["SHARP_ODDS_PATH"] = "v1/odds"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = False
        adapter = SharpSportsbookAdapter(contract)
        _MockClient.response_payload = "__default__"
        adapter.fetch_snapshot()
        self.assertIsNotNone(_MockClient.last_call)
        self.assertEqual(_MockClient.last_call[0], "https://api.sharp.app/v1/odds")

    @patch("automation_scheduler.sharp_sportsbook_adapter.httpx.Client", new=_MockClient)
    def test_http_error_mapping_and_compact_diagnostic(self):
        status_to_blocker = {404: "http_404", 401: "http_401", 403: "http_403", 429: "http_429", 502: "http_5xx"}
        for status, blocker in status_to_blocker.items():
            with self.subTest(status=status):
                os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
                os.environ["SHARP_PROVIDER_ENABLED"] = "true"
                os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
                contract = dict(self.contract)
                contract["enabled"] = True
                contract["live_calls_enabled"] = True
                contract["dry_run"] = False
                _MockClient.response_status = status
                _MockClient.response_payload = {"error": "bad route"}
                adapter = SharpSportsbookAdapter(contract)
                snapshot = adapter.fetch_snapshot()
                self.assertEqual(snapshot["status"], "provider_error")
                self.assertIn(blocker, snapshot["blockers"])
                self.assertIn("diagnostic", snapshot)
                self.assertEqual(snapshot["diagnostic"]["method"], "GET")
                self.assertTrue(snapshot["diagnostic"]["secret_redacted"])
                self.assertNotIn("error", str(snapshot.get("diagnostic", {})).lower())

    @patch("automation_scheduler.sharp_sportsbook_adapter.httpx.Client", new=_MockClient)
    def test_timeout_maps_to_provider_timeout(self):
        os.environ["SHARP_API_KEY"] = "sharp_key_1234567890"
        os.environ["SHARP_PROVIDER_ENABLED"] = "true"
        os.environ["SHARP_LIVE_READS_ENABLED"] = "true"
        contract = dict(self.contract)
        contract["enabled"] = True
        contract["live_calls_enabled"] = True
        contract["dry_run"] = False
        _MockClient.should_timeout = True
        adapter = SharpSportsbookAdapter(contract)
        snapshot = adapter.fetch_snapshot()
        self.assertEqual(snapshot["status"], "provider_error")
        self.assertIn("provider_timeout", snapshot["blockers"])


if __name__ == "__main__":
    unittest.main()
