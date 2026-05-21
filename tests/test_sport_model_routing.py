import unittest

import multi_sport_model_registry as registry


class TestSportModelRouting(unittest.TestCase):
    def test_all_15_official_sports_route(self):
        for sport in registry.OFFICIAL_SPORT_KEYS:
            config = registry.get_sport_model_config(sport)
            self.assertIsNotNone(config, sport)
            for field in [
                "sport",
                "display_name",
                "model_used",
                "model_family",
                "primary_model_type",
                "supported_markets",
                "supported_prop_categories",
                "required_inputs",
                "optional_inputs",
                "model_components",
                "officials_module",
                "simulation_method",
                "correlation_notes",
                "backtest_requirements",
                "calibration_requirements",
                "no_bet_rules",
            ]:
                self.assertIn(field, config)

    def test_esports_and_egaming_alias_route_to_esports(self):
        self.assertEqual(registry.get_sport_model_config("esports")["sport"], "esports")
        self.assertEqual(registry.get_sport_model_config("egaming")["sport"], "esports")
        self.assertTrue(registry.is_supported_sport("egaming"))

    def test_common_sport_aliases_route_to_internal_keys(self):
        expected = {
            "nba": "basketball_nba",
            "wnba": "basketball_wnba",
            "womens_nba": "basketball_wnba",
            "ncaab": "basketball_ncaab",
            "college_basketball_mens": "basketball_ncaab",
            "mens_college_basketball": "basketball_ncaab",
            "ncaawb": "basketball_ncaawb",
            "ncaaw": "basketball_ncaawb",
            "college_basketball_womens": "basketball_ncaawb",
            "womens_college_basketball": "basketball_ncaawb",
            "nfl": "americanfootball_nfl",
            "cfb": "americanfootball_ncaaf",
            "mlb": "baseball_mlb",
            "nhl": "icehockey_nhl",
            "epl": "soccer",
            "ucl": "soccer",
            "ufc": "mma_mixed_martial_arts",
            "mma": "mma_mixed_martial_arts",
            "mixed_martial_arts": "mma_mixed_martial_arts",
            "combat_sports": "mma_mixed_martial_arts",
            "boxing": "boxing",
            "pga": "golf",
            "pga_tour": "golf",
            "liv": "golf",
            "liv_golf": "golf",
            "dp_world_tour": "golf",
            "european_tour": "golf",
            "lpga": "golf",
            "valorant": "esports",
            "csgo": "esports",
            "lol": "esports",
        }
        for alias, sport_key in expected.items():
            self.assertEqual(registry.normalize_sport_key(alias), sport_key)
            self.assertEqual(registry.get_sport_model_config(alias)["sport"], sport_key)

    def test_nba_and_mlb_aliases_route(self):
        self.assertEqual(registry.get_sport_model_config("nba")["sport"], "basketball_nba")
        self.assertEqual(registry.get_sport_model_config("mlb")["sport"], "baseball_mlb")

    def test_primary_model_type_constraints(self):
        for sport in ["basketball_nba", "basketball_wnba", "basketball_ncaab", "basketball_ncaawb", "americanfootball_nfl", "americanfootball_ncaaf", "mma_mixed_martial_arts", "boxing", "golf", "formula1", "cricket", "esports"]:
            self.assertNotEqual(registry.get_sport_model_config(sport)["primary_model_type"], "poisson")
        self.assertIn("Negative Binomial", registry.get_sport_model_config("baseball_mlb")["model_family"])
        self.assertIn("Poisson", registry.get_sport_model_config("soccer")["model_family"])
        self.assertIn("Dixon Coles", " ".join(registry.get_sport_model_config("soccer")["model_components"]))
        self.assertIn("Bivariate Poisson", " ".join(registry.get_sport_model_config("soccer")["model_components"]))

    def test_sport_specific_component_requirements(self):
        hockey = registry.get_sport_model_config("icehockey_nhl")
        self.assertIn("goalie adjustment", hockey["model_components"])
        self.assertIn("special teams adjustment", hockey["model_components"])
        self.assertEqual(registry.get_sport_model_config("tennis")["primary_model_type"], "point_game_set_simulation")
        self.assertEqual(registry.get_sport_model_config("mma_mixed_martial_arts")["model_family"], "fighter_striking_grappling_finish_model")
        self.assertEqual(registry.get_sport_model_config("boxing")["model_family"], "fighter_striking_grappling_finish_model")
        self.assertEqual(registry.get_sport_model_config("golf")["model_family"], "strokes_gained_course_fit_monte_carlo_model")
        self.assertEqual(registry.get_sport_model_config("basketball_wnba")["model_family"], "wnba_possession_rating_monte_carlo_model")
        self.assertEqual(registry.get_sport_model_config("basketball_ncaab")["model_family"], "mens_college_basketball_possession_variance_model")
        self.assertEqual(registry.get_sport_model_config("basketball_ncaawb")["model_family"], "womens_college_basketball_possession_variance_model")
        self.assertEqual(registry.get_sport_model_config("formula1")["model_family"], "Race simulation")
        self.assertEqual(registry.get_sport_model_config("cricket")["model_family"], "Pitch toss innings model family")
        self.assertIn("game title routing placeholder", registry.get_sport_model_config("esports")["model_components"])

    def test_every_sport_uses_shared_officials_module_with_specific_type(self):
        for sport in registry.OFFICIAL_SPORT_KEYS:
            config = registry.get_sport_model_config(sport)
            module = config["officials_module"]
            self.assertEqual(module["module_name"], "officials_context_module")
            self.assertIn("officials_context_module", config["model_components"])
            self.assertTrue(module["official_type"])
            self.assertTrue(module["official_inputs"])
            self.assertIn(module["betting_edge_strength"], {"moderate", "weak_to_moderate", "weak", "situational"})

    def test_wnba_uses_wnba_specific_parameters_not_nba_copy(self):
        nba = registry.get_sport_model_config("basketball_nba")
        wnba = registry.get_sport_model_config("basketball_wnba")
        self.assertNotEqual(nba["sport_parameters"], wnba["sport_parameters"])
        self.assertIn("WNBA specific pace baseline", wnba["sport_parameters"]["pace_assumption"])
        self.assertIn("WNBA specific usage distribution", wnba["sport_parameters"]["usage_distribution"])

    def test_architecture_components_registered(self):
        components = registry.get_registered_architecture_components()
        self.assertIn("wee_willie_market_weakness_detector", components)
        self.assertIn("social_crowd_calibration_components", components)
        self.assertIn("provider_abstractions", components)
        self.assertIn("risk_controller", components)
        self.assertIn("alt_line_ladder_registry", components)
        self.assertTrue(all(provider["status"] == "not_configured" for provider in components["provider_abstractions"]))
        self.assertTrue(all(provider["missing_credentials_flag"] for provider in components["provider_abstractions"]))

    def test_every_sport_has_social_crowd_calibration_requirements(self):
        for sport in registry.OFFICIAL_SPORT_KEYS:
            config = registry.get_sport_model_config(sport)
            for component in registry.SOCIAL_CROWD_MODEL_COMPONENTS:
                self.assertIn(component, config["model_components"])
            for optional_input in registry.SOCIAL_CROWD_OPTIONAL_INPUTS:
                self.assertIn(optional_input, config["optional_inputs"])
            for calibration_requirement in [
                "social sentiment calibration",
                "crowdsourced signal calibration",
                "public bias adjustment",
                "rumor risk review",
                "news velocity check",
                "market narrative check",
                "sentiment versus odds movement comparison",
                "sentiment versus model probability comparison",
                "crowd consensus versus sharp market comparison",
            ]:
                self.assertIn(calibration_requirement, config["calibration_requirements"])
            for no_bet_flag in registry.SOCIAL_CROWD_NO_BET_FLAGS:
                self.assertIn(no_bet_flag, config["no_bet_rules"])

    def test_manual_ticket_and_provider_foundation_do_not_place_bets(self):
        response = registry.analyze_sport_model({"sport": "basketball_nba", "market": "moneyline"})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["manual_ticket_preview"]["status"], "manual_review_required")
        self.assertNotIn("place_bet", response["manual_ticket_preview"])

    def test_officiating_analysis_returns_clean_status_for_representative_sports(self):
        samples = {
            "basketball_nba": {"referee_name": "Crew A", "referee_data_quality": "strong", "referee_sample_size": 40},
            "americanfootball_nfl": {"referee_crew": "Crew A", "penalty_rate": 1.5},
            "baseball_mlb": {"umpire_assignment": "Ump A", "umpire_run_environment": 0.4},
            "icehockey_nhl": {"referees": "Ref A/Ref B", "linesmen": "Line A/Line B", "penalty_rate": 1.2},
            "soccer": {"referee": "Ref A", "penalty_awarded_rate": 0.7},
            "mma_mixed_martial_arts": {"referee": "Ref A", "judge_panel": "Panel A", "decision_scoring_profile": 0.5},
            "boxing": {"referee": "Ref A", "judge_panel": "Panel A", "decision_scoring_profile": 0.5},
            "tennis": {"chair_umpire": "Chair A", "time_violation_tendency": 0.2},
            "golf": {"rules_officials": "Rules A", "course_ruling_environment": "normal"},
            "formula1": {"stewards": "Panel A", "race_control": "Race Control", "penalty_tendency": 0.6},
            "cricket": {"on_field_umpires": "Ump A/Ump B", "third_umpire": "Ump C"},
            "esports": {"tournament_admin": "Admin A", "map_admin": "Map Admin", "server_admin": "Server Admin"},
        }
        for sport, official_inputs in samples.items():
            response = registry.analyze_sport_model({
                "sport": sport,
                "market": "moneyline",
                "input_stats": official_inputs,
            })
            self.assertTrue(response["ok"], sport)
            analysis = response["officiating_analysis"]
            self.assertIn(analysis["officiating_module_status"], {"inactive_base_model", "no_adjustment", "active_no_adjustment", "active_adjustment"})
            self.assertIn("officiating_summary", analysis)
            self.assertIn("officiating_logbook_fields", analysis)
            self.assertEqual(response["confirmed_bets"], [])

    def test_missing_officiating_inputs_do_not_create_500(self):
        for sport in registry.OFFICIAL_SPORT_KEYS:
            response = registry.analyze_sport_model({"sport": sport, "market": "moneyline", "input_stats": {}})
            self.assertIn("officiating_analysis", response)
            self.assertIn(response["officiating_module_status"], {"inactive_base_model", "no_adjustment"})
            self.assertNotEqual(response.get("error"), "sport_analysis_failed")

    def test_officiating_data_cannot_create_bet_by_itself(self):
        response = registry.analyze_sport_model({
            "sport": "basketball_nba",
            "market": "moneyline",
            "odds_american": 100,
            "bankroll": 500,
            "input_stats": {
                "referee_name": "Crew A",
                "home_foul_differential": 3.0,
                "referee_sample_size": 80,
                "referee_data_quality": "strong",
                "referee_adjustment_probability_points": 1.5,
            },
        })
        self.assertEqual(response["officiating_module_status"], "inactive_base_model")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertTrue(response["missing_inputs"])
        self.assertIn("base model inactive", response["officiating_no_bet_reason"])

    def test_active_nba_officiating_adjustment_is_reported_without_overriding_decision(self):
        input_stats = {
            "team": "Lakers",
            "opponent": "Nuggets",
            "selection": "Lakers",
            "home_away": "home",
            "team_pace": 101.5,
            "opponent_pace": 98.2,
            "team_offensive_rating": 115,
            "opponent_offensive_rating": 116,
            "team_defensive_rating": 114,
            "opponent_defensive_rating": 113,
            "team_efg_percent": 0.54,
            "opponent_efg_percent": 0.545,
            "team_turnover_percent": 0.155,
            "opponent_turnover_percent": 0.125,
            "team_offensive_rebound_percent": 0.25,
            "opponent_offensive_rebound_percent": 0.26,
            "team_free_throw_rate": 0.21,
            "opponent_free_throw_rate": 0.23,
            "key_player_usage_available": True,
            "minutes_projection_available": True,
            "injury_report_status": "clean",
            "referee_name": "Crew A",
            "home_foul_differential": 2.0,
            "referee_sample_size": 60,
            "referee_data_quality": "strong",
        }
        response = registry.analyze_sport_model({
            "sport": "basketball_nba",
            "event_id": "Nuggets at Lakers",
            "market": "moneyline",
            "selection": "Lakers",
            "odds_american": -120,
            "bankroll": 500,
            "input_stats": input_stats,
        })
        self.assertEqual(response["officiating_module_status"], "active_adjustment")
        self.assertTrue(response["officiating_edge_detected"])
        self.assertNotEqual(response["adjusted_true_probability"], response["true_probability"])
        self.assertEqual(response["confirmed_bets"], [])
        self.assertTrue(response["no_bets"])

    def test_officiating_does_not_break_confirmed_no_bet_mutual_exclusion(self):
        response = registry.analyze_sport_model({
            "sport": "basketball_nba",
            "event_id": "Nuggets at Lakers",
            "market": "moneyline",
            "selection": "Lakers",
            "odds_american": 100,
            "bankroll": 500,
            "input_stats": {
                "team": "Lakers",
                "opponent": "Nuggets",
                "selection": "Lakers",
                "home_away": "home",
                "team_pace": 101.5,
                "opponent_pace": 98.2,
                "team_offensive_rating": 115,
                "opponent_offensive_rating": 116,
                "team_defensive_rating": 114,
                "opponent_defensive_rating": 113,
                "team_efg_percent": 0.54,
                "opponent_efg_percent": 0.545,
                "team_turnover_percent": 0.155,
                "opponent_turnover_percent": 0.125,
                "team_offensive_rebound_percent": 0.25,
                "opponent_offensive_rebound_percent": 0.26,
                "team_free_throw_rate": 0.21,
                "opponent_free_throw_rate": 0.23,
                "key_player_usage_available": True,
                "minutes_projection_available": True,
                "injury_report_status": "clean",
                "referee_name": "Crew A",
                "referee_adjustment_probability_points": -1.5,
            },
        })
        self.assertTrue(response["confirmed_bets"])
        self.assertEqual(response["no_bets"], [])
        self.assertEqual(response["full_board_preview"]["no_bets"], [])

    def test_unsupported_sport_returns_safe_no_bet_response(self):
        response = registry.analyze_sport_model({"sport": "rugby_union", "market": "moneyline"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["confirmed_bets"], [])
        self.assertIn("unsupported sport", response["no_bet_flags"])
        self.assertEqual(response["error"], "UNSUPPORTED_SPORT")
        self.assertIn("supported_sport_keys", response)
        self.assertIn("basketball_nba", response["supported_sport_keys"])


if __name__ == "__main__":
    unittest.main()
