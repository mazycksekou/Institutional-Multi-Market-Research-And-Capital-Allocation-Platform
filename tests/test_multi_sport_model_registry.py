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
    "rugby",
    "lacrosse",
    "table_tennis",
    "badminton",
    "pickleball",
    "darts",
    "snooker",
    "volleyball",
    "handball",
    "water_polo",
    "afl",
    "icehockey_nhl",
    "tennis",
    "mma_mixed_martial_arts",
    "boxing",
    "golf",
    "formula1",
    "formula_e",
    "nascar",
    "indycar",
    "motogp",
    "cricket",
    "cs2",
    "valorant",
    "league_of_legends",
    "dota2",
    "call_of_duty",
    "overwatch",
    "esports",
]


class TestMultiSportModelRegistry(unittest.TestCase):
    def test_all_37_sports_are_present(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        self.assertEqual(len(sports), 37)
        self.assertEqual([sport["sport_key"] for sport in sports], EXPECTED_SPORT_KEYS)

    def test_mlb_is_projection_ready(self):
        mlb = registry.get_sport_model_config("baseball_mlb")
        self.assertIsNotNone(mlb)
        self.assertEqual(mlb["model_level"], "projection_ready")

    def test_only_activated_sports_allow_confirmed_bets(self):
        sports = registry.get_sports_model_registry_response()["sports"]
        enabled = [sport["sport_key"] for sport in sports if sport["confirmed_bets_allowed"]]
        self.assertEqual(enabled, ["baseball_mlb", "basketball_nba", "basketball_wnba", "basketball_ncaab", "basketball_ncaawb", "americanfootball_nfl", "americanfootball_ncaaf", "soccer", "rugby", "lacrosse", "table_tennis", "badminton", "pickleball", "darts", "snooker", "volleyball", "handball", "water_polo", "afl", "icehockey_nhl", "tennis", "mma_mixed_martial_arts", "boxing", "golf", "formula1", "formula_e", "nascar", "indycar", "motogp", "cricket", "cs2", "valorant", "league_of_legends", "dota2", "call_of_duty", "overwatch"])
        self.assertTrue(registry.confirmed_bets_allowed("baseball_mlb"))
        self.assertTrue(registry.confirmed_bets_allowed("basketball_nba"))
        self.assertTrue(registry.confirmed_bets_allowed("basketball_wnba"))
        self.assertTrue(registry.confirmed_bets_allowed("basketball_ncaab"))
        self.assertTrue(registry.confirmed_bets_allowed("basketball_ncaawb"))
        self.assertTrue(registry.confirmed_bets_allowed("americanfootball_nfl"))
        self.assertTrue(registry.confirmed_bets_allowed("americanfootball_ncaaf"))
        self.assertTrue(registry.confirmed_bets_allowed("soccer"))
        self.assertTrue(registry.confirmed_bets_allowed("rugby"))
        self.assertTrue(registry.confirmed_bets_allowed("lacrosse"))
        self.assertTrue(registry.confirmed_bets_allowed("table_tennis"))
        self.assertTrue(registry.confirmed_bets_allowed("badminton"))
        self.assertTrue(registry.confirmed_bets_allowed("pickleball"))
        self.assertTrue(registry.confirmed_bets_allowed("darts"))
        self.assertTrue(registry.confirmed_bets_allowed("snooker"))
        self.assertTrue(registry.confirmed_bets_allowed("volleyball"))
        self.assertTrue(registry.confirmed_bets_allowed("handball"))
        self.assertTrue(registry.confirmed_bets_allowed("water_polo"))
        self.assertTrue(registry.confirmed_bets_allowed("afl"))
        self.assertTrue(registry.confirmed_bets_allowed("icehockey_nhl"))
        self.assertTrue(registry.confirmed_bets_allowed("tennis"))
        self.assertTrue(registry.confirmed_bets_allowed("mma_mixed_martial_arts"))
        self.assertTrue(registry.confirmed_bets_allowed("boxing"))
        self.assertTrue(registry.confirmed_bets_allowed("golf"))
        self.assertTrue(registry.confirmed_bets_allowed("formula1"))
        self.assertTrue(registry.confirmed_bets_allowed("formula_e"))
        self.assertTrue(registry.confirmed_bets_allowed("nascar"))
        self.assertTrue(registry.confirmed_bets_allowed("indycar"))
        self.assertTrue(registry.confirmed_bets_allowed("motogp"))
        self.assertTrue(registry.confirmed_bets_allowed("cricket"))
        self.assertTrue(registry.confirmed_bets_allowed("cs2"))
        self.assertTrue(registry.confirmed_bets_allowed("valorant"))
        self.assertTrue(registry.confirmed_bets_allowed("league_of_legends"))
        self.assertTrue(registry.confirmed_bets_allowed("dota2"))
        self.assertTrue(registry.confirmed_bets_allowed("call_of_duty"))
        self.assertTrue(registry.confirmed_bets_allowed("overwatch"))
        self.assertTrue(all(
            not registry.confirmed_bets_allowed(sport["sport_key"])
            for sport in sports
            if sport["sport_key"] not in {"baseball_mlb", "basketball_nba", "basketball_wnba", "basketball_ncaab", "basketball_ncaawb", "americanfootball_nfl", "americanfootball_ncaaf", "soccer", "rugby", "lacrosse", "table_tennis", "badminton", "pickleball", "darts", "snooker", "volleyball", "handball", "water_polo", "afl", "icehockey_nhl", "tennis", "mma_mixed_martial_arts", "boxing", "golf", "formula1", "formula_e", "nascar", "indycar", "motogp", "cricket", "cs2", "valorant", "league_of_legends", "dota2", "call_of_duty", "overwatch"}
        ))

    def test_unsupported_sport_helper_behavior_is_clean(self):
        self.assertIsNone(registry.get_sport_model_config("padel"))
        self.assertFalse(registry.is_supported_sport("padel"))
        self.assertFalse(registry.confirmed_bets_allowed("padel"))
        self.assertIsNone(registry.get_required_inputs("padel"))
        self.assertIsNone(registry.get_supported_markets("padel"))
        self.assertIsNone(registry.classify_model_level("padel"))

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
        self.assertEqual(response["summary"]["total_sports"], 37)
        self.assertEqual(response["summary"]["confirmed_bet_enabled_sports"], 36)
        self.assertEqual(response["summary"]["market_derived_only_sports"], 0)
        self.assertEqual(response["summary"]["not_built_sports"], 1)
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

    def test_college_football_is_separate_active_module(self):
        college = registry.get_sport_model_config("americanfootball_ncaaf")
        nfl = registry.get_sport_model_config("americanfootball_nfl")
        self.assertTrue(college["confirmed_bets_allowed"])
        self.assertEqual(college["model_used"], "college_football_epa_drive_rating_monte_carlo_model")
        self.assertEqual(college["model_family"], "college_football_epa_drive_rating_monte_carlo_model")
        self.assertEqual(college["league_calibration_applied"], "ncaaf")
        self.assertNotEqual(college["model_family"], nfl["model_family"])
        self.assertTrue(college["input_normalizer"])
        self.assertIsInstance(college["screenshot_alias_test_payload"], dict)
        self.assertNotEqual(college["screenshot_alias_test_payload"], nfl["screenshot_alias_test_payload"])

    def test_cricket_is_standalone_active_module(self):
        cricket = registry.get_sport_model_config("cricket")
        mlb = registry.get_sport_model_config("baseball_mlb")
        self.assertTrue(cricket["confirmed_bets_allowed"])
        self.assertEqual(cricket["model_used"], "cricket_run_rate_wicket_resource_monte_carlo_model")
        self.assertEqual(cricket["model_family"], "cricket_run_rate_wicket_resource_monte_carlo_model")
        self.assertEqual(cricket["league_calibration_applied"], "cricket")
        self.assertNotEqual(cricket["model_family"], mlb["model_family"])
        self.assertTrue(cricket["input_normalizer"])
        self.assertIsInstance(cricket["screenshot_alias_test_payload"], dict)

    def test_rugby_is_standalone_active_module(self):
        rugby = registry.get_sport_model_config("rugby")
        soccer = registry.get_sport_model_config("soccer")
        nfl = registry.get_sport_model_config("americanfootball_nfl")
        self.assertTrue(rugby["confirmed_bets_allowed"])
        self.assertEqual(rugby["model_used"], "rugby_set_piece_territory_expected_points_monte_carlo_model")
        self.assertEqual(rugby["model_family"], "rugby_set_piece_territory_expected_points_monte_carlo_model")
        self.assertEqual(rugby["league_calibration_applied"], "rugby")
        self.assertNotEqual(rugby["model_family"], soccer["model_family"])
        self.assertNotEqual(rugby["model_family"], nfl["model_family"])
        self.assertTrue(rugby["input_normalizer"])
        self.assertIsInstance(rugby["screenshot_alias_test_payload"], dict)

    def test_lacrosse_is_standalone_active_module(self):
        lacrosse = registry.get_sport_model_config("lacrosse")
        rugby = registry.get_sport_model_config("rugby")
        soccer = registry.get_sport_model_config("soccer")
        self.assertTrue(lacrosse["confirmed_bets_allowed"])
        self.assertEqual(lacrosse["model_used"], "lacrosse_faceoff_possession_shot_quality_monte_carlo_model")
        self.assertEqual(lacrosse["model_family"], "lacrosse_faceoff_possession_shot_quality_monte_carlo_model")
        self.assertEqual(lacrosse["league_calibration_applied"], "lacrosse")
        self.assertNotEqual(lacrosse["model_family"], rugby["model_family"])
        self.assertNotEqual(lacrosse["model_family"], soccer["model_family"])
        self.assertTrue(lacrosse["input_normalizer"])
        self.assertIsInstance(lacrosse["screenshot_alias_test_payload"], dict)

    def test_table_tennis_is_standalone_active_module(self):
        table_tennis = registry.get_sport_model_config("table_tennis")
        tennis = registry.get_sport_model_config("tennis")
        lacrosse = registry.get_sport_model_config("lacrosse")
        self.assertTrue(table_tennis["confirmed_bets_allowed"])
        self.assertEqual(table_tennis["model_used"], "table_tennis_serve_return_rally_momentum_monte_carlo_model")
        self.assertEqual(table_tennis["model_family"], "table_tennis_serve_return_rally_momentum_monte_carlo_model")
        self.assertEqual(table_tennis["league_calibration_applied"], "table_tennis")
        self.assertNotEqual(table_tennis["model_family"], tennis["model_family"])
        self.assertNotEqual(table_tennis["model_family"], lacrosse["model_family"])
        self.assertTrue(table_tennis["input_normalizer"])
        self.assertIsInstance(table_tennis["screenshot_alias_test_payload"], dict)

    def test_badminton_is_standalone_active_module(self):
        badminton = registry.get_sport_model_config("badminton")
        table_tennis = registry.get_sport_model_config("table_tennis")
        tennis = registry.get_sport_model_config("tennis")
        self.assertTrue(badminton["confirmed_bets_allowed"])
        self.assertEqual(badminton["model_used"], "badminton_serve_return_rally_momentum_shuttle_monte_carlo_model")
        self.assertEqual(badminton["model_family"], "badminton_serve_return_rally_momentum_shuttle_monte_carlo_model")
        self.assertEqual(badminton["league_calibration_applied"], "badminton")
        self.assertNotEqual(badminton["model_family"], table_tennis["model_family"])
        self.assertNotEqual(badminton["model_family"], tennis["model_family"])
        self.assertTrue(badminton["input_normalizer"])
        self.assertIsInstance(badminton["screenshot_alias_test_payload"], dict)

    def test_pickleball_is_standalone_active_module(self):
        pickleball = registry.get_sport_model_config("pickleball")
        tennis = registry.get_sport_model_config("tennis")
        badminton = registry.get_sport_model_config("badminton")
        table_tennis = registry.get_sport_model_config("table_tennis")
        self.assertTrue(pickleball["confirmed_bets_allowed"])
        self.assertEqual(pickleball["model_used"], "pickleball_dink_kitchen_serve_return_monte_carlo_model")
        self.assertEqual(pickleball["model_family"], "pickleball_dink_kitchen_serve_return_monte_carlo_model")
        self.assertEqual(pickleball["league_calibration_applied"], "pickleball")
        self.assertNotEqual(pickleball["model_family"], tennis["model_family"])
        self.assertNotEqual(pickleball["model_family"], badminton["model_family"])
        self.assertNotEqual(pickleball["model_family"], table_tennis["model_family"])
        self.assertTrue(pickleball["input_normalizer"])
        self.assertIsInstance(pickleball["screenshot_alias_test_payload"], dict)

    def test_snooker_is_standalone_active_module(self):
        snooker = registry.get_sport_model_config("snooker")
        darts = registry.get_sport_model_config("darts")
        pickleball = registry.get_sport_model_config("pickleball")
        self.assertTrue(snooker["confirmed_bets_allowed"])
        self.assertEqual(snooker["model_used"], "snooker_frame_break_safety_potting_monte_carlo_model")
        self.assertEqual(snooker["model_family"], "snooker_frame_break_safety_potting_monte_carlo_model")
        self.assertEqual(snooker["league_calibration_applied"], "snooker")
        self.assertNotEqual(snooker["model_family"], darts["model_family"])
        self.assertNotEqual(snooker["model_family"], pickleball["model_family"])
        self.assertTrue(snooker["input_normalizer"])
        self.assertIsInstance(snooker["screenshot_alias_test_payload"], dict)

    def test_darts_is_standalone_active_module(self):
        darts = registry.get_sport_model_config("darts")
        badminton = registry.get_sport_model_config("badminton")
        pickleball = registry.get_sport_model_config("pickleball")
        table_tennis = registry.get_sport_model_config("table_tennis")
        self.assertTrue(darts["confirmed_bets_allowed"])
        self.assertEqual(darts["model_used"], "darts_checkout_scoring_pressure_leg_set_monte_carlo_model")
        self.assertEqual(darts["model_family"], "darts_checkout_scoring_pressure_leg_set_monte_carlo_model")
        self.assertEqual(darts["league_calibration_applied"], "darts")
        self.assertNotEqual(darts["model_family"], badminton["model_family"])
        self.assertNotEqual(darts["model_family"], pickleball["model_family"])
        self.assertNotEqual(darts["model_family"], table_tennis["model_family"])
        self.assertTrue(darts["input_normalizer"])
        self.assertIsInstance(darts["screenshot_alias_test_payload"], dict)

    def test_volleyball_is_standalone_active_module(self):
        volleyball = registry.get_sport_model_config("volleyball")
        table_tennis = registry.get_sport_model_config("table_tennis")
        basketball = registry.get_sport_model_config("basketball_nba")
        self.assertTrue(volleyball["confirmed_bets_allowed"])
        self.assertEqual(volleyball["model_used"], "volleyball_sideout_attack_block_serve_monte_carlo_model")
        self.assertEqual(volleyball["model_family"], "volleyball_sideout_attack_block_serve_monte_carlo_model")
        self.assertEqual(volleyball["league_calibration_applied"], "volleyball")
        self.assertNotEqual(volleyball["model_family"], table_tennis["model_family"])
        self.assertNotEqual(volleyball["model_family"], basketball["model_family"])
        self.assertTrue(volleyball["input_normalizer"])
        self.assertIsInstance(volleyball["screenshot_alias_test_payload"], dict)

    def test_handball_is_standalone_active_module(self):
        handball = registry.get_sport_model_config("handball")
        volleyball = registry.get_sport_model_config("volleyball")
        soccer = registry.get_sport_model_config("soccer")
        self.assertTrue(handball["confirmed_bets_allowed"])
        self.assertEqual(handball["model_used"], "handball_fastbreak_goalkeeper_efficiency_monte_carlo_model")
        self.assertEqual(handball["model_family"], "handball_fastbreak_goalkeeper_efficiency_monte_carlo_model")
        self.assertEqual(handball["league_calibration_applied"], "handball")
        self.assertNotEqual(handball["model_family"], volleyball["model_family"])
        self.assertNotEqual(handball["model_family"], soccer["model_family"])
        self.assertTrue(handball["input_normalizer"])
        self.assertIsInstance(handball["screenshot_alias_test_payload"], dict)

    def test_afl_is_standalone_active_module(self):
        afl = registry.get_sport_model_config("afl")
        rugby = registry.get_sport_model_config("rugby")
        lacrosse = registry.get_sport_model_config("lacrosse")
        cricket = registry.get_sport_model_config("cricket")
        self.assertTrue(afl["confirmed_bets_allowed"])
        self.assertEqual(afl["model_used"], "afl_clearance_inside50_scoring_shot_monte_carlo_model")
        self.assertEqual(afl["model_family"], "afl_clearance_inside50_scoring_shot_monte_carlo_model")
        self.assertEqual(afl["league_calibration_applied"], "afl")
        self.assertNotEqual(afl["model_family"], rugby["model_family"])
        self.assertNotEqual(afl["model_family"], lacrosse["model_family"])
        self.assertNotEqual(afl["model_family"], cricket["model_family"])
        self.assertTrue(afl["input_normalizer"])
        self.assertIsInstance(afl["screenshot_alias_test_payload"], dict)

    def test_cs2_is_standalone_active_module(self):
        cs2 = registry.get_sport_model_config("cs2")
        esports = registry.get_sport_model_config("esports")
        self.assertTrue(cs2["confirmed_bets_allowed"])
        self.assertEqual(cs2["model_used"], "cs2_round_economy_map_pool_monte_carlo_model")
        self.assertEqual(cs2["model_family"], "cs2_round_economy_map_pool_monte_carlo_model")
        self.assertEqual(cs2["league_calibration_applied"], "cs2")
        self.assertNotEqual(cs2["model_family"], esports["model_family"])
        self.assertTrue(cs2["input_normalizer"])
        self.assertIsInstance(cs2["screenshot_alias_test_payload"], dict)

    def test_valorant_is_standalone_active_module(self):
        valorant = registry.get_sport_model_config("valorant")
        cs2 = registry.get_sport_model_config("cs2")
        esports = registry.get_sport_model_config("esports")
        self.assertTrue(valorant["confirmed_bets_allowed"])
        self.assertEqual(valorant["model_used"], "valorant_agent_composition_economy_map_pool_monte_carlo_model")
        self.assertEqual(valorant["model_family"], "valorant_agent_composition_economy_map_pool_monte_carlo_model")
        self.assertEqual(valorant["league_calibration_applied"], "valorant")
        self.assertNotEqual(valorant["model_family"], cs2["model_family"])
        self.assertNotEqual(valorant["model_family"], esports["model_family"])
        self.assertTrue(valorant["input_normalizer"])
        self.assertIsInstance(valorant["screenshot_alias_test_payload"], dict)

    def test_league_of_legends_is_standalone_active_module(self):
        lol = registry.get_sport_model_config("league_of_legends")
        valorant = registry.get_sport_model_config("valorant")
        esports = registry.get_sport_model_config("esports")
        self.assertTrue(lol["confirmed_bets_allowed"])
        self.assertEqual(lol["model_used"], "league_of_legends_draft_objective_gold_monte_carlo_model")
        self.assertEqual(lol["model_family"], "league_of_legends_draft_objective_gold_monte_carlo_model")
        self.assertEqual(lol["league_calibration_applied"], "league_of_legends")
        self.assertNotEqual(lol["model_family"], valorant["model_family"])
        self.assertNotEqual(lol["model_family"], esports["model_family"])
        self.assertTrue(lol["input_normalizer"])
        self.assertIsInstance(lol["screenshot_alias_test_payload"], dict)

    def test_dota2_is_standalone_active_module(self):
        dota2 = registry.get_sport_model_config("dota2")
        lol = registry.get_sport_model_config("league_of_legends")
        esports = registry.get_sport_model_config("esports")
        self.assertTrue(dota2["confirmed_bets_allowed"])
        self.assertEqual(dota2["model_used"], "dota2_draft_lane_objective_roshan_monte_carlo_model")
        self.assertEqual(dota2["model_family"], "dota2_draft_lane_objective_roshan_monte_carlo_model")
        self.assertEqual(dota2["league_calibration_applied"], "dota2")
        self.assertNotEqual(dota2["model_family"], lol["model_family"])
        self.assertNotEqual(dota2["model_family"], esports["model_family"])
        self.assertTrue(dota2["input_normalizer"])
        self.assertIsInstance(dota2["screenshot_alias_test_payload"], dict)

    def test_call_of_duty_is_standalone_active_module(self):
        cod = registry.get_sport_model_config("call_of_duty")
        dota2 = registry.get_sport_model_config("dota2")
        esports = registry.get_sport_model_config("esports")
        self.assertTrue(cod["confirmed_bets_allowed"])
        self.assertEqual(cod["model_used"], "call_of_duty_map_mode_rotation_respawn_snd_monte_carlo_model")
        self.assertEqual(cod["model_family"], "call_of_duty_map_mode_rotation_respawn_snd_monte_carlo_model")
        self.assertEqual(cod["league_calibration_applied"], "call_of_duty")
        self.assertNotEqual(cod["model_family"], dota2["model_family"])
        self.assertNotEqual(cod["model_family"], esports["model_family"])
        self.assertTrue(cod["input_normalizer"])
        self.assertIsInstance(cod["screenshot_alias_test_payload"], dict)

    def test_overwatch_is_standalone_active_module(self):
        overwatch = registry.get_sport_model_config("overwatch")
        cod = registry.get_sport_model_config("call_of_duty")
        esports = registry.get_sport_model_config("esports")
        self.assertTrue(overwatch["confirmed_bets_allowed"])
        self.assertEqual(overwatch["model_used"], "overwatch_hero_composition_map_mode_objective_monte_carlo_model")
        self.assertEqual(overwatch["model_family"], "overwatch_hero_composition_map_mode_objective_monte_carlo_model")
        self.assertEqual(overwatch["league_calibration_applied"], "overwatch")
        self.assertNotEqual(overwatch["model_family"], cod["model_family"])
        self.assertNotEqual(overwatch["model_family"], esports["model_family"])
        self.assertTrue(overwatch["input_normalizer"])
        self.assertIsInstance(overwatch["screenshot_alias_test_payload"], dict)

    def test_formula1_is_standalone_active_module(self):
        f1 = registry.get_sport_model_config("formula1")
        cricket = registry.get_sport_model_config("cricket")
        self.assertTrue(f1["confirmed_bets_allowed"])
        self.assertEqual(f1["model_used"], "f1_qualifying_race_pace_pit_strategy_monte_carlo_model")
        self.assertEqual(f1["model_family"], "f1_qualifying_race_pace_pit_strategy_monte_carlo_model")
        self.assertEqual(f1["league_calibration_applied"], "f1")
        self.assertNotEqual(f1["model_family"], cricket["model_family"])
        self.assertTrue(f1["input_normalizer"])
        self.assertIsInstance(f1["screenshot_alias_test_payload"], dict)

    def test_formula_e_is_standalone_active_module(self):
        formula_e = registry.get_sport_model_config("formula_e")
        f1 = registry.get_sport_model_config("formula1")
        nascar = registry.get_sport_model_config("nascar")
        self.assertTrue(formula_e["confirmed_bets_allowed"])
        self.assertEqual(formula_e["model_used"], "formula_e_energy_management_attack_mode_street_circuit_monte_carlo_model")
        self.assertEqual(formula_e["model_family"], "formula_e_energy_management_attack_mode_street_circuit_monte_carlo_model")
        self.assertEqual(formula_e["league_calibration_applied"], "formula_e")
        self.assertNotEqual(formula_e["model_family"], f1["model_family"])
        self.assertNotEqual(formula_e["model_family"], nascar["model_family"])
        self.assertTrue(formula_e["input_normalizer"])
        self.assertIsInstance(formula_e["screenshot_alias_test_payload"], dict)

    def test_nascar_is_standalone_active_module(self):
        nascar = registry.get_sport_model_config("nascar")
        f1 = registry.get_sport_model_config("formula1")
        self.assertTrue(nascar["confirmed_bets_allowed"])
        self.assertEqual(nascar["model_used"], "nascar_track_position_speed_rating_pit_variance_monte_carlo_model")
        self.assertEqual(nascar["model_family"], "nascar_track_position_speed_rating_pit_variance_monte_carlo_model")
        self.assertEqual(nascar["league_calibration_applied"], "nascar")
        self.assertNotEqual(nascar["model_family"], f1["model_family"])
        self.assertTrue(nascar["input_normalizer"])
        self.assertIsInstance(nascar["screenshot_alias_test_payload"], dict)

    def test_f1_indycar_and_motogp_are_separate_active_modules(self):
        f1 = registry.get_sport_model_config("formula1")
        indycar = registry.get_sport_model_config("indycar")
        motogp = registry.get_sport_model_config("motogp")
        self.assertTrue(f1["confirmed_bets_allowed"])
        self.assertTrue(indycar["confirmed_bets_allowed"])
        self.assertTrue(motogp["confirmed_bets_allowed"])
        self.assertEqual(f1["model_used"], "f1_qualifying_race_pace_pit_strategy_monte_carlo_model")
        self.assertEqual(indycar["model_used"], "indycar_aero_strategy_restart_pit_variance_monte_carlo_model")
        self.assertEqual(motogp["model_used"], "motogp_rider_bike_tire_weather_monte_carlo_model")
        self.assertEqual(f1["league_calibration_applied"], "f1")
        self.assertEqual(indycar["league_calibration_applied"], "indycar")
        self.assertEqual(motogp["league_calibration_applied"], "motogp")
        self.assertEqual(len({f1["model_family"], indycar["model_family"], motogp["model_family"]}), 3)
        self.assertTrue(f1["input_normalizer"])
        self.assertTrue(indycar["input_normalizer"])
        self.assertTrue(motogp["input_normalizer"])
        self.assertNotEqual(f1["screenshot_alias_test_payload"], indycar["screenshot_alias_test_payload"])
        self.assertNotEqual(indycar["screenshot_alias_test_payload"], motogp["screenshot_alias_test_payload"])

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
            "rugby": ("referee/TMO", "moderate"),
            "lacrosse": ("officials", "weak"),
            "table_tennis": ("umpire/referee", "weak"),
            "badminton": ("umpire/service judge", "weak"),
            "pickleball": ("referee", "weak"),
            "darts": ("caller/referee", "weak"),
            "volleyball": ("first ref/second ref", "weak"),
            "handball": ("referee pair", "weak_to_moderate"),
            "mma_mixed_martial_arts": ("referee and judges", "moderate"),
            "boxing": ("referee and judges", "moderate"),
            "tennis": ("chair umpire", "weak_to_moderate"),
            "golf": ("rules officials", "weak"),
            "formula1": ("stewards/race control", "situational"),
            "formula_e": ("stewards/race control", "situational"),
            "nascar": ("race control/NASCAR officials", "situational"),
            "indycar": ("race control/IndyCar officials", "situational"),
            "motogp": ("race direction/stewards", "situational"),
            "cs2": ("tournament admin/server/map veto enforcement", "weak"),
            "valorant": ("tournament admin/server/map veto enforcement", "weak"),
            "league_of_legends": ("tournament admin/side selection/rule enforcement", "weak"),
            "dota2": ("tournament admin/server/rule enforcement", "weak"),
            "call_of_duty": ("tournament admin/server/map-mode enforcement", "weak"),
            "overwatch": ("tournament admin/server/map-mode enforcement", "weak"),
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
