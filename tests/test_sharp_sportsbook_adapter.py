import os
import unittest

from src.connectors.errors import ConnectorDisabledError
from automation_scheduler.sharp_sportsbook_adapter import SharpSportsbookAdapter
from automation_scheduler.sportsbook_odds_provider import summarize_sportsbook_snapshot


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
        os.environ.pop("SHARP_API_BASE_URL", None)
        os.environ.pop("SHARP_API_TIMEOUT_SECONDS", None)
        os.environ.pop("SHARP_EVENTS_PATH", None)
        os.environ.pop("SHARP_ODDS_PATH", None)
        os.environ.pop("SHARP_PLAYER_PROPS_PATH", None)
        os.environ.pop("SHARP_SPORTS_PATH", None)

    def test_validate_config_reports_disabled_boundary(self):
        adapter = SharpSportsbookAdapter(self.contract)
        cfg = adapter.validate_config()
        self.assertFalse(cfg["ok"])
        self.assertEqual(cfg["status"], "provider_disabled")
        self.assertIn("provider_disabled", cfg["blockers"])
        self.assertIn("live_reads_disabled", cfg["blockers"])
        self.assertIn("blocked_missing_credentials", cfg["blockers"])
        self.assertIn("read_only_required", cfg["blockers"])
        self.assertEqual(cfg["credential_status"], "disabled")

    def test_fetch_snapshot_returns_disabled_placeholder(self):
        adapter = SharpSportsbookAdapter(self.contract)
        snapshot = adapter.fetch_snapshot()
        self.assertTrue(snapshot["ok"])
        self.assertEqual(snapshot["status"], "provider_disabled")
        self.assertEqual(snapshot["records"], [])
        self.assertEqual(snapshot["records_received"], 0)
        self.assertEqual(snapshot["records_valid"], 0)
        self.assertEqual(snapshot["records_rejected"], 0)
        self.assertIn("provider_disabled", snapshot["blockers"])
        self.assertEqual(snapshot["connector_configuration"]["provider"], "odds_data")
        self.assertEqual(snapshot["connector_readiness"]["status"], "disabled")

    def test_health_summary_compact_no_secret_leak(self):
        adapter = SharpSportsbookAdapter(self.contract)
        summary = summarize_sportsbook_snapshot(adapter.health_check())
        self.assertFalse(summary["provider_enabled"])
        self.assertFalse(summary["live_calls_enabled"])
        self.assertEqual(summary["credential_status"], "disabled")
        self.assertNotIn("sharp_key_1234567890", str(summary))

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

    def test_path_joining_helpers_remain_stable(self):
        os.environ["SHARP_API_BASE_URL"] = "https://api.sharp.app///"
        os.environ["SHARP_ODDS_PATH"] = "v1/odds"
        adapter = SharpSportsbookAdapter(self.contract)
        diag = adapter.build_sharp_url("odds_path")
        self.assertEqual(diag["url_path"], "/v1/odds")

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

    def test_live_flat_shape_aliases_normalize(self):
        adapter = SharpSportsbookAdapter(self.contract)
        normalized, warnings, reject = adapter._normalize_flattened_row(
            {
                "event": {
                    "event_id": "evt_live",
                    "sport": "baseball",
                    "league": "MLB",
                    "event_start_time": "2026-05-28T00:00:00+00:00",
                    "sportsbook": "sharp",
                },
                "market": {
                    "market_type": "moneyline",
                    "selection": "Home",
                    "odds_american": -115,
                    "wire_received_at": "2026-05-28T00:00:00+00:00",
                },
                "book": {},
                "outcome": {},
            }
        )
        self.assertIsNone(reject)
        self.assertEqual(normalized["market"], "moneyline")
        self.assertEqual(normalized["odds"], -115)
        self.assertGreater(normalized["implied_probability"], 0)
        self.assertIn("fallback_event_name", warnings)

    def test_disabled_fetch_methods_raise(self):
        adapter = SharpSportsbookAdapter(self.contract)
        for method_name in ["fetch_events", "fetch_odds", "fetch_player_props", "fetch_sports"]:
            with self.subTest(method=method_name):
                with self.assertRaises(ConnectorDisabledError):
                    getattr(adapter, method_name)()


if __name__ == "__main__":
    unittest.main()
