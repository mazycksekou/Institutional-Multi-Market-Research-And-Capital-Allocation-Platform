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

    def test_egaming_alias_endpoint_returns_esports(self):
        response = asyncio.run(action_analyze_sport_model(SportAnalysisRequest(sport="egaming", market="match winner")))
        self.assertEqual(response["sport"], "esports")
        self.assertEqual(response["confirmed_bets"], [])

    def test_route_is_in_openapi(self):
        operation = app.openapi()["paths"]["/api/actions/models/sport-analysis"]["post"]
        self.assertEqual(operation["operationId"], "analyzeSportModel")


if __name__ == "__main__":
    unittest.main()
