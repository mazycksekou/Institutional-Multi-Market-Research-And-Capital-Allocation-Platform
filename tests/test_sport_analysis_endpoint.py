import asyncio
import unittest

from main import SportAnalysisRequest, action_analyze_sport_model, app


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

    def test_required_inputs_without_backtest_are_research_only(self):
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
        self.assertEqual(response["component_statuses"]["possession_expected_score_model"], "research_mode_not_bettable")
        self.assertIn("no backtest proof", response["no_bet_flags"])
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

    def test_weak_source_quality_creates_no_bet_flag_with_strong_crowd(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(
            sport="basketball_nba",
            market="moneyline",
            input_stats={"crowd_consensus": 84, "source_quality": "weak"},
        )))
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
