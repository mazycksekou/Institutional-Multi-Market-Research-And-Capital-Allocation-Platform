import json
import os
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch

from automation_scheduler import ncaaf_collegefootballdata_adapter as adapter
from automation_scheduler.data_paths import AUTOMATION_DATA_DIR_ENV


SAMPLE_GAME = {
    "id": 401520100,
    "season": 2025,
    "week": 1,
    "seasonType": "regular",
    "homeTeam": "Ohio State",
    "awayTeam": "Texas",
    "homeConference": "Big Ten",
    "awayConference": "SEC",
    "venue": "Ohio Stadium",
    "neutralSite": False,
    "homePoints": 24,
    "awayPoints": 17,
    "completed": True,
}

SAMPLE_ADVANCED_HOME = {
    "gameId": 401520100,
    "season": 2025,
    "week": 1,
    "team": "Ohio State",
    "opponent": "Texas",
    "offense": {"ppa": 0.23, "successRate": 0.49, "explosiveness": 1.44, "plays": 72, "drives": 12},
    "defense": {"ppa": -0.08, "successRate": 0.37, "explosiveness": 1.1, "drives": 11},
}

SAMPLE_ADVANCED_AWAY = {
    "gameId": 401520100,
    "season": 2025,
    "week": 1,
    "team": "Texas",
    "opponent": "Ohio State",
    "offense": {"ppa": 0.11, "successRate": 0.41, "explosiveness": 1.22, "plays": 68, "drives": 11},
    "defense": {"ppa": 0.02, "successRate": 0.45, "explosiveness": 1.31, "drives": 12},
}

SAMPLE_HAVOC_HOME = {
    "gameId": 401520100,
    "season": 2025,
    "week": 1,
    "team": "Ohio State",
    "opponent": "Texas",
    "offense": {"havocRate": 0.12},
    "defense": {"havocRate": 0.18},
}

SAMPLE_HAVOC_AWAY = {
    "gameId": 401520100,
    "season": 2025,
    "week": 1,
    "team": "Texas",
    "opponent": "Ohio State",
    "offense": {"havocRate": 0.16},
    "defense": {"havocRate": 0.13},
}


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class _EndpointRouter:
    def __init__(self, payloads_by_path):
        self.payloads_by_path = payloads_by_path
        self.paths = []

    def __call__(self, request, timeout=10):
        path = urllib.parse.urlparse(request.full_url).path
        self.paths.append(path)
        return _FakeResponse(self.payloads_by_path.get(path, []))


class TestNcaafCollegeFootballDataAdapter(unittest.TestCase):
    def _without_cfbd_key(self):
        os.environ.pop(adapter.CFBD_API_KEY_ENV, None)

    def test_metadata_only_verification_works_without_key_and_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                self._without_cfbd_key()
                result = adapter.verify_ncaaf_cfbd_adapter(fetch_live_sample=False, max_records=5)

            self.assertTrue(result["ok"])
            self.assertEqual(result["adapter_status"], "metadata_only_verified")
            self.assertFalse(result["enabled"])
            self.assertTrue(result["missing_api_key"])
            self.assertFalse(result["fetch_live_sample_performed"])
            self.assertFalse(result["provider_write"])
            self.assertFalse(result["execution_allowed"])
            self.assertFalse(result["raw_payload_included"])
            self.assertFalse(result["secrets_included"])
            paths = result["report_paths"]
            self.assertTrue(Path(paths["latest_path"]).exists())
            self.assertTrue(Path(paths["item_path"]).exists())
            self.assertIn("data_sources", paths["latest_path"])
            persisted = Path(paths["latest_path"]).read_text(encoding="utf-8").lower()
            self.assertNotIn("provider_payload", persisted)
            self.assertNotIn("raw_provider_payload", persisted)

    def test_missing_key_live_request_is_clean_and_makes_no_external_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                self._without_cfbd_key()
                with patch("automation_scheduler.ncaaf_collegefootballdata_adapter.urllib.request.urlopen") as urlopen:
                    result = adapter.verify_ncaaf_cfbd_adapter(fetch_live_sample=True, max_records=5)

        self.assertEqual(result["adapter_status"], "missing_api_key")
        self.assertTrue(result["missing_api_key"])
        self.assertFalse(result["fetch_live_sample_performed"])
        urlopen.assert_not_called()
        self.assertNotIn("key_value", str(result).lower())

    def test_fetch_live_false_makes_no_external_request_even_when_key_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {AUTOMATION_DATA_DIR_ENV: tmp, adapter.CFBD_API_KEY_ENV: "do-not-leak"}
            with patch.dict(os.environ, env, clear=False):
                with patch("automation_scheduler.ncaaf_collegefootballdata_adapter.urllib.request.urlopen") as urlopen:
                    result = adapter.verify_ncaaf_cfbd_adapter(fetch_live_sample=False, max_records=5)

        self.assertEqual(result["adapter_status"], "metadata_only_verified")
        self.assertTrue(result["api_key_configured"])
        self.assertFalse(result["missing_api_key"])
        self.assertFalse(result["fetch_live_sample_performed"])
        self.assertNotIn("do-not-leak", str(result))
        urlopen.assert_not_called()

    def test_live_sample_is_capped_at_25_and_key_is_never_returned(self):
        rows = [dict(SAMPLE_GAME, id=401520100 + idx) for idx in range(40)]
        with tempfile.TemporaryDirectory() as tmp:
            env = {AUTOMATION_DATA_DIR_ENV: tmp, adapter.CFBD_API_KEY_ENV: "do-not-leak"}
            with patch.dict(os.environ, env, clear=False):
                with patch(
                    "automation_scheduler.ncaaf_collegefootballdata_adapter.urllib.request.urlopen",
                    return_value=_FakeResponse(rows),
                ):
                    result = adapter.verify_ncaaf_cfbd_adapter(fetch_live_sample=True, max_records=100)

        self.assertEqual(result["adapter_status"], "live_sample_verified")
        self.assertEqual(result["max_records_effective"], 25)
        self.assertEqual(result["sample_records_received"], 25)
        self.assertEqual(result["sample_records_normalized"], 25)
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        rendered = str(result)
        self.assertNotIn("do-not-leak", rendered)
        self.assertNotIn("authorization", rendered.lower())

    def test_targeted_advanced_sample_hard_caps_provider_calls_and_maps_new_fields(self):
        router = _EndpointRouter(
            {
                "/games": [SAMPLE_GAME],
                "/stats/game/advanced": [SAMPLE_ADVANCED_HOME, SAMPLE_ADVANCED_AWAY],
                "/stats/game/havoc": [SAMPLE_HAVOC_HOME, SAMPLE_HAVOC_AWAY],
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            env = {AUTOMATION_DATA_DIR_ENV: tmp, adapter.CFBD_API_KEY_ENV: "do-not-leak"}
            with patch.dict(os.environ, env, clear=False):
                with patch("automation_scheduler.ncaaf_collegefootballdata_adapter.urllib.request.urlopen", side_effect=router):
                    result = adapter.verify_ncaaf_cfbd_adapter(
                        fetch_live_sample=True,
                        sample_profile="targeted_advanced_tiny",
                        season=2025,
                        week=1,
                        max_records=5,
                        max_provider_calls=99,
                        include_games=True,
                        include_team_stats=True,
                        include_advanced_stats=True,
                        include_rankings=True,
                        include_lines=True,
                    )
                    persisted = Path(result["report_paths"]["latest_path"]).read_text(encoding="utf-8").lower()

        self.assertEqual(router.paths, ["/games", "/stats/game/advanced", "/stats/game/havoc"])
        self.assertEqual(result["adapter_status"], "live_sample_verified")
        self.assertEqual(result["provider_calls_made"], 3)
        self.assertEqual(result["max_provider_calls_effective"], 3)
        self.assertEqual(result["skipped_endpoints_due_to_call_budget"], ["sp_ratings", "lines"])
        self.assertEqual(result["records_received_by_endpoint"]["games"], 1)
        self.assertEqual(result["records_normalized_by_endpoint"]["advanced_stats"], 2)
        self.assertIn("home_offensive_epa_per_play", result["newly_supported_model_inputs"])
        self.assertIn("away_offensive_epa_per_play", result["newly_supported_model_inputs"])
        self.assertIn("home_points_per_drive", result["newly_supported_model_inputs"])
        self.assertIn("away_havoc_rate", result["newly_supported_model_inputs"])
        self.assertGreater(result["coverage_score_after"], result["coverage_score_before"])
        self.assertGreater(result["calibration_readiness_after"], result["calibration_readiness_before"])
        self.assertFalse(result["enabled"])
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertEqual(result["execution_allowed_count"], 0)
        rendered = str(result)
        self.assertNotIn("do-not-leak", rendered)
        self.assertNotIn("authorization", rendered.lower())
        self.assertNotIn("do-not-leak", persisted)
        self.assertNotIn('"raw_payload":', persisted)
        self.assertNotIn("provider_payload", persisted)
        self.assertNotIn("records_by_endpoint", persisted)

    def test_targeted_advanced_default_call_budget_skips_uncalled_endpoints(self):
        router = _EndpointRouter({"/games": [SAMPLE_GAME]})
        with tempfile.TemporaryDirectory() as tmp:
            env = {AUTOMATION_DATA_DIR_ENV: tmp, adapter.CFBD_API_KEY_ENV: "do-not-leak"}
            with patch.dict(os.environ, env, clear=False):
                with patch("automation_scheduler.ncaaf_collegefootballdata_adapter.urllib.request.urlopen", side_effect=router):
                    result = adapter.verify_ncaaf_cfbd_adapter(
                        fetch_live_sample=True,
                        sample_profile="targeted_advanced_tiny",
                        season=2025,
                        week=1,
                        max_records=5,
                        include_games=True,
                        include_team_stats=True,
                        include_advanced_stats=True,
                    )

        self.assertEqual(router.paths, ["/games"])
        self.assertEqual(result["provider_calls_made"], 1)
        self.assertEqual(result["max_provider_calls_effective"], 1)
        self.assertEqual(result["skipped_endpoints_due_to_call_budget"], ["advanced_stats", "team_havoc_stats"])
        self.assertNotIn("home_offensive_epa_per_play", result["covered_model_inputs"])

    def test_targeted_advanced_missing_key_is_clean_and_makes_no_external_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                self._without_cfbd_key()
                with patch("automation_scheduler.ncaaf_collegefootballdata_adapter.urllib.request.urlopen") as urlopen:
                    result = adapter.verify_ncaaf_cfbd_adapter(
                        fetch_live_sample=True,
                        sample_profile="targeted_advanced_tiny",
                        max_records=5,
                        max_provider_calls=3,
                        include_games=True,
                        include_team_stats=True,
                        include_advanced_stats=True,
                    )

        self.assertEqual(result["adapter_status"], "missing_api_key")
        self.assertEqual(result["provider_calls_made"], 0)
        self.assertEqual(result["endpoints_called"], [])
        self.assertFalse(result["fetch_live_sample_performed"])
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["raw_payload_included"])
        self.assertFalse(result["secrets_included"])
        urlopen.assert_not_called()

    def test_game_record_normalizes_and_maps_without_fabricating_missing_fields(self):
        normalized = adapter.normalize_cfbd_game_record(SAMPLE_GAME)
        self.assertEqual(normalized["game_id"], "401520100")
        self.assertEqual(normalized["event_id"], "401520100")
        self.assertEqual(normalized["season"], 2025)
        self.assertEqual(normalized["week"], 1)
        self.assertEqual(normalized["home_team"], "Ohio State")
        self.assertEqual(normalized["away_team"], "Texas")
        self.assertEqual(normalized["home_points"], 24)
        self.assertEqual(normalized["away_points"], 17)
        self.assertEqual(normalized["final_result"]["winner"], "home")

        mapping = adapter.map_cfbd_to_ncaaf_model_inputs([normalized])
        self.assertIn("event_id", mapping["model_inputs_supported"])
        self.assertIn("season", mapping["model_inputs_supported"])
        self.assertIn("week", mapping["model_inputs_supported"])
        self.assertIn("home_team", mapping["covered_model_inputs"])
        self.assertIn("away_team", mapping["covered_model_inputs"])
        self.assertIn("neutral_site", mapping["covered_model_inputs"])
        self.assertIn("final_score", mapping["outcome_fields_available"])
        self.assertIn("home_offensive_epa_per_play", mapping["missing_required_inputs"])
        self.assertIn("weather_temperature", mapping["missing_optional_inputs"])
        self.assertNotIn("injuries", mapping["covered_model_inputs"])
        self.assertNotIn("officials", mapping["covered_model_inputs"])

    def test_advanced_record_maps_stats_only_when_present(self):
        raw = {
            "gameId": 401520100,
            "season": 2025,
            "week": 1,
            "team": "Ohio State",
            "opponent": "Texas",
            "side": "home",
            "offense": {"ppa": 0.23, "successRate": 0.49, "explosiveness": 1.44},
            "defense": {"ppa": -0.08, "successRate": 0.37, "explosiveness": 1.1},
        }
        normalized = adapter.normalize_cfbd_advanced_record(raw)
        self.assertEqual(normalized["home_offensive_epa_per_play"], 0.23)
        self.assertEqual(normalized["home_success_rate"], 0.49)
        self.assertEqual(normalized["home_defensive_success_rate_allowed"], 0.37)

        mapping = adapter.map_cfbd_to_ncaaf_model_inputs([normalized])
        self.assertIn("home_offensive_epa_per_play", mapping["covered_model_inputs"])
        self.assertIn("home_success_rate", mapping["covered_model_inputs"])
        self.assertIn("away_offensive_epa_per_play", mapping["missing_required_inputs"])

    def test_report_writer_compacts_secret_like_and_raw_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                paths = adapter.write_cfbd_sample_report(
                    {
                        "run_id": "unit_test",
                        "adapter_status": "metadata_only_verified",
                        "source_id": adapter.SOURCE_ID,
                        "module": adapter.MODULE,
                        "api_key": "do-not-leak",
                        "raw_payload": {"provider": "drop"},
                        "records": [{"game_id": "1"}],
                    }
                )
                latest = Path(paths["latest_path"]).read_text(encoding="utf-8").lower()
                self.assertNotIn("do-not-leak", latest)
                self.assertNotIn('"raw_payload"', latest)
                self.assertNotIn("drop", latest)
                self.assertIn("records", latest)
                self.assertIn("game_id", latest)

    def test_config_is_disabled_by_default_and_registry_compatible(self):
        config = adapter.get_cfbd_config()
        self.assertEqual(config["source_id"], adapter.SOURCE_ID)
        self.assertEqual(config["module"], adapter.MODULE)
        self.assertEqual(config["source_access_type"], "free_key")
        self.assertIn(config["approval_status"], {"needs_review", "candidate", "approved_for_research"})
        self.assertFalse(config["enabled"])
        self.assertFalse(config["provider_write"])
        self.assertFalse(config["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
