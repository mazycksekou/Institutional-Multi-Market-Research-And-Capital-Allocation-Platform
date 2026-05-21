import asyncio
import unittest

import multi_sport_model_registry as registry
from main import action_get_sports_model_registry, app


EXPECTED_SPORT_KEYS = [
    "baseball_mlb",
    "basketball_nba",
    "basketball_wnba",
    "basketball_ncaab",
    "basketball_ncaawb",
    "americanfootball_nfl",
    "americanfootball_ncaaf",
    "soccer",
    "icehockey_nhl",
    "tennis",
    "mma_mixed_martial_arts",
    "boxing",
    "golf",
    "formula1",
    "cricket",
    "esports",
]


class TestMultiSportModelRegistry(unittest.TestCase):
    def test_all_16_sports_are_present(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        self.assertEqual(len(sports), 16)
        self.assertEqual([sport["sport_key"] for sport in sports], EXPECTED_SPORT_KEYS)

    def test_mlb_is_projection_ready(self):
        mlb = registry.get_sport_model_config("baseball_mlb")
        self.assertIsNotNone(mlb)
        self.assertEqual(mlb["model_level"], "projection_ready")

    def test_only_activated_sports_allow_confirmed_bets(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        enabled = [sport["sport_key"] for sport in sports if sport["confirmed_bets_allowed"]]
        self.assertEqual(enabled, ["baseball_mlb", "basketball_nba", "basketball_wnba", "basketball_ncaab", "basketball_ncaawb", "americanfootball_nfl", "soccer", "icehockey_nhl", "tennis", "mma_mixed_martial_arts", "boxing", "golf"])
        self.assertTrue(registry.confirmed_bets_allowed("baseball_mlb"))
        self.assertTrue(registry.confirmed_bets_allowed("basketball_nba"))
        self.assertTrue(registry.confirmed_bets_allowed("basketball_wnba"))
        self.assertTrue(registry.confirmed_bets_allowed("basketball_ncaab"))
        self.assertTrue(registry.confirmed_bets_allowed("basketball_ncaawb"))
        self.assertTrue(registry.confirmed_bets_allowed("americanfootball_nfl"))
        self.assertTrue(registry.confirmed_bets_allowed("soccer"))
        self.assertTrue(registry.confirmed_bets_allowed("icehockey_nhl"))
        self.assertTrue(registry.confirmed_bets_allowed("tennis"))
        self.assertTrue(registry.confirmed_bets_allowed("mma_mixed_martial_arts"))
        self.assertTrue(registry.confirmed_bets_allowed("boxing"))
        self.assertTrue(registry.confirmed_bets_allowed("golf"))
        self.assertTrue(all(
            not registry.confirmed_bets_allowed(sport["sport_key"])
            for sport in sports
            if sport["sport_key"] not in {"baseball_mlb", "basketball_nba", "basketball_wnba", "basketball_ncaab", "basketball_ncaawb", "americanfootball_nfl", "soccer", "icehockey_nhl", "tennis", "mma_mixed_martial_arts", "boxing", "golf"}
        ))

    def test_unsupported_sport_helper_behavior_is_clean(self):
        self.assertIsNone(registry.get_sport_model_config("rugby_union"))
        self.assertFalse(registry.is_supported_sport("rugby_union"))
        self.assertFalse(registry.confirmed_bets_allowed("rugby_union"))
        self.assertIsNone(registry.get_required_inputs("rugby_union"))
        self.assertIsNone(registry.get_supported_markets("rugby_union"))
        self.assertIsNone(registry.classify_model_level("rugby_union"))

    def test_required_helper_functions_work(self):
        self.assertTrue(registry.is_supported_sport("baseball_mlb"))
        self.assertTrue(registry.confirmed_bets_allowed("baseball_mlb"))
        self.assertEqual(registry.classify_model_level("baseball_mlb"), "projection_ready")
        self.assertIsInstance(registry.get_required_inputs("baseball_mlb"), list)
        self.assertIn("moneyline", registry.get_supported_markets("baseball_mlb"))

    def test_endpoint_model_response_shape_validates(self):
        response = asyncio.run(action_get_sports_model_registry())
        self.assertTrue(response["ok"])
        self.assertEqual(response["endpoint"], "getSportsModelRegistry")
        self.assertEqual(response["summary"]["total_sports"], 16)
        self.assertEqual(response["summary"]["confirmed_bet_enabled_sports"], 12)
        self.assertEqual(response["summary"]["market_derived_only_sports"], 0)
        self.assertEqual(response["summary"]["not_built_sports"], 4)
        self.assertEqual(response["error"], None)
        self.assertEqual(response["detail"], None)

    def test_no_duplicate_sport_keys(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        keys = [sport["sport_key"] for sport in sports]
        self.assertEqual(len(keys), len(set(keys)))

    def test_supported_markets_exist_for_each_sport(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        for sport in sports:
            self.assertIn("supported_markets", sport)
            self.assertGreater(len(sport["supported_markets"]), 0)

    def test_supported_props_exist_for_each_sport_even_if_empty(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        for sport in sports:
            self.assertIn("supported_props", sport)
            self.assertIsInstance(sport["supported_props"], list)

    def test_provider_needs_exist_for_each_sport(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        for sport in sports:
            self.assertIn("provider_needs", sport)
            self.assertGreater(len(sport["provider_needs"]), 0)

    def test_active_confirmed_sports_register_input_normalization_contract(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        for sport in sports:
            if not sport["confirmed_bets_allowed"]:
                continue
            with self.subTest(sport=sport["sport_key"]):
                self.assertTrue(sport.get("input_normalizer"))
                self.assertIsInstance(sport.get("screenshot_alias_test_payload"), dict)
                self.assertTrue((sport["screenshot_alias_test_payload"].get("input_stats") or {}))

    def test_wnba_mens_and_womens_college_basketball_are_separate_modules(self):
        wnba = registry.get_sport_model_config("basketball_wnba")
        mens = registry.get_sport_model_config("basketball_ncaab")
        womens = registry.get_sport_model_config("basketball_ncaawb")
        self.assertEqual(wnba["model_name"] if "model_name" in wnba else wnba["model_used"], "wnba_possession_rating_monte_carlo_model")
        self.assertEqual(mens["model_used"], "mens_college_basketball_possession_variance_model")
        self.assertEqual(womens["model_used"], "womens_college_basketball_possession_variance_model")
        self.assertEqual(wnba["league_calibration_applied"], "wnba")
        self.assertEqual(mens["league_calibration_applied"], "ncaab")
        self.assertEqual(womens["league_calibration_applied"], "ncaawb")
        self.assertEqual(len({wnba["model_family"], mens["model_family"], womens["model_family"]}), 3)
        self.assertNotEqual(wnba["screenshot_alias_test_payload"], mens["screenshot_alias_test_payload"])
        self.assertNotEqual(mens["screenshot_alias_test_payload"], womens["screenshot_alias_test_payload"])

    def test_log_fields_exist_for_each_sport(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        for sport in sports:
            self.assertIn("log_fields_required", sport)
            self.assertIn("sport_key", sport["log_fields_required"])
            self.assertIn("decision", sport["log_fields_required"])

    def test_global_rules_are_included(self):
        response = registry.get_sports_model_registry_response()
        self.assertEqual(response["global_rules"], registry.GLOBAL_MODEL_REGISTRY_RULES)
        self.assertIn("Market-derived-only probabilities cannot create confirmed bets.", response["global_rules"])

    def test_officials_module_uses_sport_specific_official_type(self):
        expected = {
            "basketball_nba": ("referee crew", "moderate"),
            "americanfootball_nfl": ("referee crew", "moderate"),
            "baseball_mlb": ("umpire crew", "moderate"),
            "icehockey_nhl": ("referees and linesmen", "moderate"),
            "soccer": ("referee", "moderate"),
            "mma_mixed_martial_arts": ("referee and judges", "moderate"),
            "boxing": ("referee and judges", "moderate"),
            "tennis": ("chair umpire", "weak_to_moderate"),
            "golf": ("rules officials", "weak"),
            "formula1": ("stewards/race control", "situational"),
            "esports": ("tournament admin/map/server/rule enforcement", "weak"),
        }
        for sport_key, (official_type, edge_strength) in expected.items():
            module = registry.get_sport_model_config(sport_key)["officials_module"]
            self.assertEqual(module["module_name"], "officials_context_module")
            self.assertTrue(module["same_module_for_all_sports"])
            self.assertEqual(module["official_type"], official_type)
            self.assertEqual(module["betting_edge_strength"], edge_strength)

    def test_route_is_in_openapi_with_descriptions(self):
        schema = app.openapi()
        operation = schema["paths"]["/api/actions/models/sports-registry"]["get"]
        self.assertEqual(operation["operationId"], "getSportsModelRegistry")
        sports_schema = schema["components"]["schemas"]["SportModelConfigResponse"]["properties"]
        self.assertIn("description", sports_schema["model_level"])
        self.assertIn("description", sports_schema["confirmed_bets_allowed"])
        self.assertIn("description", sports_schema["officials_module"])


if __name__ == "__main__":
    unittest.main()
