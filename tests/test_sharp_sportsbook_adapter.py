import os
import unittest
from datetime import datetime, timezone

from src.connectors.errors import ConnectorDisabledError
from src.connectors.odds_data import describe_odds_data_connector_readiness
from src.providers.sportsbooks.adapters import normalize_sportsbook_event, normalize_sportsbook_odds
from src.services.odds_runtime_bridge import SharpSportsbookAdapter, summarize_sportsbook_snapshot


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
        self.assertEqual(cfg["credential_status"], "missing_credentials")

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
        self.assertEqual(summary["credential_status"], "missing_credentials")
        self.assertNotIn("sharp_key_1234567890", str(summary))

    def test_build_sharp_url_diagnostic_redacted(self):
        adapter = SharpSportsbookAdapter(self.contract)
        diag = adapter.build_sharp_url("odds_path")
        self.assertEqual(diag["provider"], "sharp_sportsbook")
        self.assertEqual(diag["path_name"], "odds_path")
        self.assertTrue(diag["read_only"])
        self.assertFalse(diag["live_access_enabled"])
        self.assertEqual(diag["connector_readiness"]["status"], "disabled")
        self.assertEqual(describe_odds_data_connector_readiness()["status"], "disabled")

    def test_path_joining_helpers_remain_stable(self):
        adapter = SharpSportsbookAdapter(self.contract)
        diag = adapter.build_sharp_url("odds_path")
        self.assertEqual(diag["path_name"], "odds_path")
        self.assertIn("provider_disabled", diag["blockers"])
        self.assertIn("read_only_required", diag["blockers"])

    def test_malformed_payload_rejected(self):
        adapter = SharpSportsbookAdapter(self.contract)
        verdict = adapter.validate_payload(
            {
                "event_id": "evt1",
                "market": "moneyline",
                "selection": "A",
                "odds": "bad",
                "timestamp": "2026-05-28T00:00:00+00:00",
            }
        )
        self.assertFalse(verdict["ok"])
        self.assertIn("malformed_odds", verdict["errors"])

    def test_decimal_odds_normalize_and_probability(self):
        normalized = normalize_sportsbook_odds(
            "sharp_sportsbook",
            event_id="evt2",
            sport_key="soccer_epl",
            market="moneyline",
            sportsbook="sharp",
            selection="X",
            price_american=-150,
            point=None,
            last_update=datetime.now(timezone.utc).isoformat(),
            raw={"event_id": "evt2"},
        )
        self.assertEqual(normalized["provider"], "sharp_sportsbook")
        self.assertEqual(normalized["market"], "moneyline")
        self.assertEqual(normalized["price_american"], -150)
        self.assertAlmostEqual(normalized["price_decimal"], 1.666667, places=6)
        self.assertAlmostEqual(normalized["implied_probability"], 0.6, places=6)

    def test_live_flat_shape_aliases_normalize(self):
        normalized = normalize_sportsbook_event(
            "sharp_sportsbook",
            {
                "id": "evt_live",
                "sport_key": "soccer_epl",
                "sport_title": "Premier League",
                "commence_time": "2026-05-28T00:00:00+00:00",
                "home_team": "Home",
                "away_team": "Away",
            },
            league="EPL",
        )
        self.assertEqual(normalized["provider"], "sharp_sportsbook")
        self.assertEqual(normalized["event_id"], "evt_live")
        self.assertEqual(normalized["league"], "EPL")
        self.assertEqual(normalized["sport_key"], "soccer_epl")

    def test_disabled_fetch_methods_raise(self):
        adapter = SharpSportsbookAdapter(self.contract)
        for method_name in ["fetch_events", "fetch_odds", "fetch_player_props", "fetch_sports"]:
            with self.subTest(method=method_name):
                with self.assertRaises(ConnectorDisabledError):
                    getattr(adapter, method_name)()


if __name__ == "__main__":
    unittest.main()
