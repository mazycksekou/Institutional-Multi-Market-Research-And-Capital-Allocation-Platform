import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import SportAnalysisRequest, action_analyze_sport_model, app, require_action_key


class TestSportAnalysisEndpoint(unittest.TestCase):
    def test_response_contains_required_fields(self):
        payload = SportAnalysisRequest(
            sport="baseball_mlb",
            market="moneyline",
            event_id="evt_1",
            odds_american=-110,
            bankroll=1000,
            unit_size=25,
            input_stats={},
        )
        response = asyncio.run(action_analyze_sport_model(payload))
        for field in [
            "sport",
            "model_used",
            "model_family",
            "market",
            "projected_score",
            "true_probability",
            "implied_probability",
            "edge",
            "confidence",
            "risk_level",
            "recommended_unit_size",
            "no_bet_flags",
            "correlation_notes",
            "model_components",
            "missing_inputs",
            "backtest_status",
            "calibration_status",
            "logbook_ready_row",
            "component_statuses",
            "advanced_edge_components",
            "provider_needs",
            "risk_controller",
            "wee_willie_market_weakness_detector",
            "social_sentiment_engine",
            "crowdsourced_signal_engine",
            "public_bias_detector",
            "news_velocity_detector",
            "rumor_risk_filter",
            "market_narrative_tracker",
            "sentiment_calibration_status",
            "crowd_signal_calibration_status",
            "sentiment_no_bet_flags",
            "manual_ticket_preview",
            "full_board_preview",
        ]:
            self.assertIn(field, response)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertIn("required inputs missing", response["no_bet_flags"])

    def test_legacy_nba_inputs_without_modern_core_are_inactive_missing_data(self):
        input_stats = {
            "pace": 99,
            "offensive rating": 116,
            "defensive rating": 112,
            "Four Factors": {},
            "player usage": {},
            "minutes projection": {},
            "injury report": {},
            "sport_model_probability": 0.57,
        }
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            odds_american=-110,
            input_stats=input_stats,
            bankroll=1000,
            unit_size=25,
        )))
        self.assertEqual(response["component_statuses"]["possession_expected_score_model"], "inactive_missing_data")
        self.assertIn("team", response["missing_inputs"])
        self.assertIn("required inputs missing", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_social_and_crowd_conflicts_are_no_bet_calibration_flags(self):
        input_stats = {
            "pace": 99,
            "offensive rating": 116,
            "defensive rating": 112,
            "Four Factors": {},
            "player usage": {},
            "minutes projection": {},
            "injury report": {},
            "sport_model_probability": 0.57,
            "social_sentiment": 95,
            "crowd_consensus": 0.35,
            "public_betting_percent": 82,
            "sharp_money_percent": 45,
            "news_velocity": 90,
            "rumor_risk": "unconfirmed",
            "injury_rumor": True,
            "market_narrative": 88,
            "beat_writer_signal": "unverified",
            "source_quality": "low",
        }
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            odds_american=-110,
            input_stats=input_stats,
            bankroll=1000,
            unit_size=25,
        )))
        self.assertEqual(response["confirmed_bets"], [])
        self.assertIn("crowd consensus conflicts with model probability", response["sentiment_no_bet_flags"])
        self.assertIn("public bias likely inflated price", response["sentiment_no_bet_flags"])
        self.assertIn("news velocity spike without verified source", response["sentiment_no_bet_flags"])
        self.assertIn("rumor not confirmed", response["sentiment_no_bet_flags"])
        self.assertEqual(response["social_sentiment_engine"]["component_status"], "research_mode_not_bettable")
        self.assertEqual(response["crowdsourced_signal_engine"]["component_status"], "research_mode_not_bettable")
        self.assertEqual(
            response["social_crowd_signal_explanation"]["detected_inputs"]["social_sentiment"],
            95,
        )
        self.assertEqual(
            response["social_crowd_signal_explanation"]["detected_inputs"]["crowd_consensus"],
            0.35,
        )
        self.assertEqual(
            response["social_sentiment_engine"]["signal_explanation"]["standalone_bet_reason_allowed"],
            False,
        )
        self.assertIn(response["social_sentiment_engine"]["signal_explanation"]["support_status"], {
            "conflicts_with_model",
            "requires_manual_review",
            "supports_model",
        })

    def test_social_sentiment_from_input_stats_is_detected(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={"social_sentiment": 61},
        )))
        self.assertEqual(response["social_sentiment_engine"]["component_status"], "research_mode_not_bettable")
        self.assertNotIn("sentiment data unavailable", response["sentiment_no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_crowd_consensus_from_input_stats_is_detected(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={"crowd_consensus": 0.64},
        )))
        self.assertEqual(response["crowdsourced_signal_engine"]["component_status"], "research_mode_not_bettable")
        self.assertNotIn("crowdsourced signal unavailable", response["sentiment_no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_rumor_risk_creates_no_bet_flag(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={"rumor_risk": "unconfirmed"},
        )))
        self.assertIn("rumor not confirmed", response["sentiment_no_bet_flags"])
        self.assertIn("rumor not confirmed", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_public_bias_creates_no_bet_flag(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={"public_betting_percent": 82, "sharp_money_percent": 44},
        )))
        self.assertIn("public bias likely inflated price", response["sentiment_no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_accepts_numeric_public_percentages(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            odds_american=-110,
            bankroll=1000,
            unit_size=25,
            input_stats={"public_betting_percent": 78, "public_money_percent": 62, "sharp_money_percent": 38},
        )))
        self.assertIn("public bias likely inflated price", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_accepts_string_percentages(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            odds_american="-110",
            bankroll="1000",
            unit_size="25",
            input_stats={
                "public_betting_percent": "78 percent",
                "public_money_percent": "62 percent",
                "sharp_money_percent": "38 percent",
                "news_velocity": "82 percent",
            },
        )))
        self.assertIn("public bias likely inflated price", response["no_bet_flags"])
        self.assertIn("news velocity spike without verified source", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_weak_source_quality_creates_no_bet_flag_with_strong_crowd(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={"crowd_consensus": 84, "source_quality": "weak"},
        )))
        self.assertIn("sentiment source quality too low", response["sentiment_no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_source_quality_strong_maps_to_90(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={
                "social_sentiment": "neutral",
                "crowd_consensus": "neutral",
                "source_quality": "strong",
                "verified_news_source": True,
            },
        )))
        self.assertEqual(
            response["social_crowd_signal_explanation"]["detected_inputs"]["source_quality"],
            90,
        )

    def test_neutral_crowd_verified_source_does_not_require_manual_review(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={
                "social_sentiment": "neutral",
                "crowd_consensus": "neutral",
                "news_velocity": "medium",
                "source_quality": "strong",
                "verified_news_source": True,
            },
        )))
        self.assertEqual(
            response["social_crowd_signal_explanation"]["support_status"],
            "neutral_calibrated",
        )
        self.assertNotIn("social signal not backtested", response["sentiment_no_bet_flags"])
        self.assertNotIn("crowd signal not calibrated", response["sentiment_no_bet_flags"])
        self.assertNotIn("sentiment data unavailable", response["sentiment_no_bet_flags"])
        self.assertNotIn("crowdsourced signal unavailable", response["sentiment_no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_heavy_public_lean_weak_source_requires_manual_review(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={
                "social_sentiment": "hyped public side",
                "crowd_consensus": "heavy public lean",
                "source_quality": "weak",
            },
        )))
        self.assertEqual(
            response["social_crowd_signal_explanation"]["support_status"],
            "requires_manual_review",
        )
        self.assertIn("sentiment source quality too low", response["sentiment_no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_missing_social_data_still_returns_inactive_missing_data(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={},
        )))
        self.assertEqual(response["social_sentiment_engine"]["component_status"], "inactive_missing_data")
        self.assertIn("sentiment data unavailable", response["sentiment_no_bet_flags"])
        self.assertIn("crowdsourced signal unavailable", response["sentiment_no_bet_flags"])

    def test_handles_missing_input_stats(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
        )))
        self.assertIn("input_stats_missing_or_invalid", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_handles_null_input_stats(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats=None,
        )))
        self.assertIn("input_stats_missing_or_invalid", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_handles_unsupported_sport_with_safe_no_bet_response(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="lacrosse",
            market="moneyline",
            bankroll="1000",
            unit_size="25",
            input_stats={"social_sentiment": "strong"},
        )))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "UNSUPPORTED_SPORT")
        self.assertIn("unsupported sport", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_never_raises_unhandled_exception_for_malformed_input(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market=123,
            odds_american="bad odds",
            bankroll="not money",
            unit_size="not units",
            input_stats=["not", "a", "dict"],
        )))
        self.assertIn("ok", response)
        self.assertIn("endpoint", response)
        self.assertIn("error", response)
        self.assertIn("detail", response)
        self.assertIn("confirmed_bets", response)
        self.assertIn("no_bet_flags", response)
        self.assertIn("input_stats_missing_or_invalid", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_route_exception_returns_safe_envelope(self):
        with patch("main.multi_sport_model_registry.analyze_sport_model", side_effect=RuntimeError("secret-token")):
            response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
                sport="basketball_nba",
                market="moneyline",
            )))
        self.assertFalse(response["ok"])
        self.assertEqual(response["endpoint"], "analyzeSportModel")
        self.assertEqual(response["error"], "sport_analysis_failed")
        self.assertIn("internal_error_handled", response["no_bet_flags"])
        self.assertNotIn("secret-token", response["detail"])
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["target_lines"], [])
        self.assertEqual(response["no_bets"], [])

    def test_social_crowd_only_signals_cannot_create_confirmed_bets(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            odds_american="-110",
            input_stats={
                "social_sentiment": 95,
                "crowd_consensus": 92,
                "public_betting_percent": "78 percent",
                "sharp_money_percent": "80 percent",
                "source_quality": "high",
            },
        )))
        self.assertEqual(response["confirmed_bets"], [])

    def test_text_social_crowd_scores_do_not_crash_direct_handler(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="nba",
            market="moneyline",
            input_stats={
                "crowd_consensus": "heavy public lean",
                "news_velocity": "high",
                "social_sentiment": "hyped public side",
            },
        )))
        self.assertTrue(response["ok"])
        self.assertEqual(response["sport"], "basketball_nba")
        self.assertEqual(
            response["social_crowd_signal_explanation"]["detected_inputs"]["crowd_consensus"],
            85,
        )
        self.assertEqual(
            response["social_crowd_signal_explanation"]["detected_inputs"]["news_velocity"],
            90,
        )
        self.assertEqual(
            response["social_crowd_signal_explanation"]["detected_inputs"]["social_sentiment"],
            85,
        )
        self.assertIn("news velocity spike without verified source", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_text_social_crowd_scores_do_not_crash_post_endpoint(self):
        app.dependency_overrides[require_action_key] = lambda: None
        try:
            client = TestClient(app)
            response = client.post(
                "/api/actions/models/sport-analysis",
                json={
                    "sport": "nba",
                    "market": "moneyline",
                    "input_stats": {
                        "crowd_consensus": "heavy public lean",
                        "news_velocity": "high",
                        "social_sentiment": "hyped public side",
                    },
                },
            )
        finally:
            app.dependency_overrides.pop(require_action_key, None)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["sport"], "basketball_nba")
        self.assertEqual(payload["confirmed_bets"], [])

    def test_post_endpoint_common_sport_aliases(self):
        app.dependency_overrides[require_action_key] = lambda: None
        try:
            client = TestClient(app)
            cases = {
                "nba": "basketball_nba",
                "soccer": "soccer",
                "rugby": "rugby",
                "rugby_union": "rugby",
                "rugby_league": "rugby",
                "nrl": "rugby",
                "super_rugby": "rugby",
                "six_nations": "rugby",
                "premiership_rugby": "rugby",
                "united_rugby_championship": "rugby",
                "rugby_world_cup": "rugby",
                "top_14": "rugby",
                "mlb": "baseball_mlb",
                "ufc": "mma_mixed_martial_arts",
                "mma": "mma_mixed_martial_arts",
                "mixed_martial_arts": "mma_mixed_martial_arts",
                "combat_sports": "mma_mixed_martial_arts",
                "boxing": "boxing",
                "wnba": "basketball_wnba",
                "womens_nba": "basketball_wnba",
                "ncaab": "basketball_ncaab",
                "mens_college_basketball": "basketball_ncaab",
                "ncaawb": "basketball_ncaawb",
                "ncaaw": "basketball_ncaawb",
                "womens_college_basketball": "basketball_ncaawb",
                "ncaaf": "americanfootball_ncaaf",
                "college_football": "americanfootball_ncaaf",
                "cfb": "americanfootball_ncaaf",
                "ncaa_football": "americanfootball_ncaaf",
                "pga": "golf",
                "liv_golf": "golf",
                "dp_world_tour": "golf",
                "lpga": "golf",
                "ipl": "cricket",
                "t20_cricket": "cricket",
                "odi": "cricket",
                "test_cricket": "cricket",
                "bbl": "cricket",
                "the_hundred": "cricket",
                "cpl": "cricket",
                "psl": "cricket",
                "formula_1": "formula1",
                "f1": "formula1",
                "fia_formula_1": "formula1",
                "grand_prix": "formula1",
                "motorsport_f1": "formula1",
                "formula_e": "formula_e",
                "formulae": "formula_e",
                "fe": "formula_e",
                "fia_formula_e": "formula_e",
                "abb_formula_e": "formula_e",
                "electric_racing": "formula_e",
                "motorsport_formula_e": "formula_e",
                "nascar_cup": "nascar",
                "cup_series": "nascar",
                "nascar_cup_series": "nascar",
                "xfinity_series": "nascar",
                "nascar_xfinity": "nascar",
                "truck_series": "nascar",
                "nascar_trucks": "nascar",
                "craftsman_truck_series": "nascar",
                "stock_car_racing": "nascar",
                "motorsport_nascar": "nascar",
                "indy_car": "indycar",
                "ntt_indycar": "indycar",
                "ntt_indycar_series": "indycar",
                "indycar_series": "indycar",
                "indianapolis_500": "indycar",
                "indy_500": "indycar",
                "motorsport_indycar": "indycar",
                "moto_gp": "motogp",
                "fim_motogp": "motogp",
                "grand_prix_motorcycle": "motogp",
                "motorcycle_racing": "motogp",
                "motorsport_motogp": "motogp",
                "cs2": "cs2",
                "counter_strike_2": "cs2",
                "counterstrike2": "cs2",
                "counter_strike": "cs2",
                "csgo": "cs2",
                "counterstrike": "cs2",
                "esports_cs2": "cs2",
                "valorant": "valorant",
                "val": "valorant",
                "riot_valorant": "valorant",
                "esports_valorant": "valorant",
                "vct": "valorant",
                "valorant_champions_tour": "valorant",
                "league_of_legends": "league_of_legends",
                "lol": "league_of_legends",
                "league": "league_of_legends",
                "riot_lol": "league_of_legends",
                "esports_lol": "league_of_legends",
                "lcs": "league_of_legends",
                "lec": "league_of_legends",
                "lck": "league_of_legends",
                "lpl": "league_of_legends",
                "worlds": "league_of_legends",
                "msi": "league_of_legends",
                "dota2": "dota2",
                "dota_2": "dota2",
                "dota": "dota2",
                "esports_dota2": "dota2",
                "dota_pro_circuit": "dota2",
                "dpc": "dota2",
                "the_international": "dota2",
                "ti": "dota2",
                "call_of_duty": "call_of_duty",
                "cod": "call_of_duty",
                "cdl": "call_of_duty",
                "esports_cod": "call_of_duty",
                "cod_league": "call_of_duty",
                "callofduty": "call_of_duty",
                "call_of_duty_league": "call_of_duty",
                "overwatch": "overwatch",
                "overwatch2": "overwatch",
                "overwatch_2": "overwatch",
                "ow": "overwatch",
                "ow2": "overwatch",
                "esports_overwatch": "overwatch",
                "overwatch_league": "overwatch",
                "owl": "overwatch",
                "overwatch_champions_series": "overwatch",
                "owcs": "overwatch",
            }
            for submitted, expected in cases.items():
                response = client.post(
                    "/api/actions/models/sport-analysis",
                    json={"sport": submitted, "market": "moneyline", "input_stats": {}},
                )
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["sport"], expected)
                self.assertEqual(payload["confirmed_bets"], [])
        finally:
            app.dependency_overrides.pop(require_action_key, None)

    def test_response_always_includes_action_safe_fields(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={"social_sentiment": 60},
        )))
        for field in ["ok", "endpoint", "error", "detail", "confirmed_bets", "no_bet_flags"]:
            self.assertIn(field, response)

    def test_egaming_alias_endpoint_returns_esports(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(sport="egaming", market="match winner")))
        self.assertEqual(response["sport"], "esports")
        self.assertEqual(response["confirmed_bets"], [])

    def test_sport_analysis_still_works_for_esports(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="esports",
            market="match winner",
            input_stats={"social_sentiment": 52, "crowd_consensus": 0.58},
        )))
        self.assertEqual(response["sport"], "esports")
        self.assertEqual(response["model_used"], "game_specific_esports_router")
        self.assertEqual(response["confirmed_bets"], [])

    def test_route_is_in_openapi(self):
        operation = app.openapi()["paths"]["/api/actions/models/sport-analysis"]["post"]
        self.assertEqual(operation["operationId"], "analyzeSportModel")


if __name__ == "__main__":
    unittest.main()
