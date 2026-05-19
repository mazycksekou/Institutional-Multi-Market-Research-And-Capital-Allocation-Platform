import asyncio
import unittest

from fastapi.testclient import TestClient

from full_board_engine import build_full_board_preview
from main import (
    ScreenshotAnalysisRequest,
    SportAnalysisRequest,
    action_analyze_sport_model,
    action_analyze_ticket_screenshot,
    app,
    require_action_key,
)


NBA_MISSING_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "team_pace",
    "opponent_pace",
    "team_offensive_rating",
    "opponent_offensive_rating",
    "team_defensive_rating",
    "opponent_defensive_rating",
    "team_efg_percent",
    "opponent_efg_percent",
    "team_turnover_percent",
    "opponent_turnover_percent",
    "team_offensive_rebound_percent",
    "opponent_offensive_rebound_percent",
    "team_free_throw_rate",
    "opponent_free_throw_rate",
    "key_player_usage_available",
    "minutes_projection_available",
    "injury_report_status",
]


def nba_full_inputs(**extra):
    data = {
        "team": "Celtics",
        "opponent": "Knicks",
        "selection": "Celtics",
        "home_away": "home",
        "team_pace": 101.5,
        "opponent_pace": 98.2,
        "team_offensive_rating": 121.0,
        "opponent_offensive_rating": 113.0,
        "team_defensive_rating": 110.0,
        "opponent_defensive_rating": 116.0,
        "team_efg_percent": 0.575,
        "opponent_efg_percent": 0.535,
        "team_turnover_percent": 0.118,
        "opponent_turnover_percent": 0.136,
        "team_offensive_rebound_percent": 0.285,
        "opponent_offensive_rebound_percent": 0.245,
        "team_free_throw_rate": 0.235,
        "opponent_free_throw_rate": 0.205,
        "key_player_usage_available": True,
        "minutes_projection_available": True,
        "injury_report_status": "clean",
    }
    data.update(extra)
    return data


def sport_payload(**extra):
    payload = {
        "sport": "basketball_nba",
        "league": "basketball_nba",
        "market": "moneyline",
        "event_id": "Knicks at Celtics",
        "odds_american": -110,
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "standard",
        "input_stats": nba_full_inputs(),
    }
    payload.update(extra)
    return payload


def nba_lakers_balanced_inputs(**extra):
    data = nba_full_inputs(
        team="Lakers",
        opponent="Nuggets",
        selection="Lakers",
        team_offensive_rating=115,
        opponent_offensive_rating=116,
        team_defensive_rating=114,
        opponent_defensive_rating=113,
        team_efg_percent=0.54,
        opponent_efg_percent=0.545,
        team_turnover_percent=0.155,
        opponent_turnover_percent=0.125,
        team_offensive_rebound_percent=0.25,
        opponent_offensive_rebound_percent=0.26,
        team_free_throw_rate=0.21,
        opponent_free_throw_rate=0.23,
        home_away="home",
    )
    data.update(extra)
    return data


class TestNbaModelActivation(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**sport_payload(**extra))))

    def _screenshot(self, **extra):
        payload = {
            "source_type": "chatgpt_parsed",
            "sport": "nba",
            "league": "nba",
            "event": "Knicks at Celtics",
            "teams": ["Knicks", "Celtics"],
            "market": "moneyline",
            "selection": "Celtics",
            "odds_american": -110,
            "book": "DraftKings",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "standard",
            "input_stats": nba_full_inputs(),
        }
        payload.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    def test_nba_missing_inputs_returns_partial_mode_and_exact_missing_inputs(self):
        response = self._screenshot(input_stats={})
        self.assertTrue(response["partial_model_mode"])
        self.assertEqual(response["missing_inputs"], NBA_MISSING_INPUTS)
        self.assertEqual(response["suggested_stake"], 0)
        self.assertEqual(response["confirmed_bets"], [])

    def test_nba_full_inputs_returns_active_or_evaluated_model_output(self):
        response = self._sport()
        self.assertIn(response["model_status"], {"active", "evaluated"})
        self.assertEqual(response["component_statuses"]["possession_expected_score_model"], "active")
        self.assertEqual(response["missing_inputs"], [])
        self.assertIn("required_core_inputs", response["nba_input_contract"])
        self.assertIn("optional_enrichment_inputs", response["nba_input_contract"])

    def test_nba_full_inputs_returns_estimated_true_probability(self):
        response = self._sport()
        self.assertIsNotNone(response["estimated_true_probability"])
        self.assertGreater(response["estimated_true_probability"], 0)
        self.assertLess(response["estimated_true_probability"], 1)

    def test_nba_full_inputs_returns_edge(self):
        response = self._sport()
        self.assertIsNotNone(response["edge"])
        self.assertIsNotNone(response["implied_probability"])
        self.assertIsNotNone(response["confidence"])

    def test_nba_core_present_optional_missing_still_active_lower_confidence(self):
        response = self._sport()
        self.assertEqual(response["model_status"], "active")
        self.assertTrue(response["input_coverage"]["optional_enrichment_missing"])
        self.assertLess(response["confidence"], 95)

    def test_nba_modern_optional_package_increases_coverage(self):
        rich_inputs = nba_full_inputs(
            projected_game_pace=99.6,
            team_recent_net_rating_5=3.7,
            opponent_recent_net_rating_5=1.3,
            team_recent_net_rating_10=2.6,
            opponent_recent_net_rating_10=4.2,
            team_rest_days=2,
            opponent_rest_days=1,
            team_back_to_back=False,
            opponent_back_to_back=True,
            team_travel_distance_miles=0,
            opponent_travel_distance_miles=1420,
            team_projected_points=116.1,
            opponent_projected_points=113.8,
            projected_margin=2.3,
            projected_total=229.9,
            opening_odds=-110,
            best_available_odds=-120,
            consensus_odds=-125,
            public_betting_percent=52,
            public_money_percent=51,
            sharp_money_percent=49,
            referee_name="Test Referee",
            foul_rate_per_game=41.8,
            free_throw_rate_allowed=0.238,
            home_foul_differential=0.7,
            referee_sample_size=44,
            referee_data_quality="strong",
        )
        response = self._sport(input_stats=rich_inputs)
        self.assertEqual(response["model_status"], "active")
        self.assertGreater(len(response["input_coverage"]["optional_enrichment_present"]), 5)
        self.assertGreater(len(response["input_coverage"]["provider_enrichment_present"]), 1)
        self.assertGreater(len(response["input_coverage"]["referee_present"]), 1)

    def test_nba_spread_requires_line_in_addition_to_core(self):
        response = self._sport(market="spread", input_stats=nba_full_inputs(market_type="spread"))
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertIn("line", response["missing_inputs"])

    def test_nba_no_edge_returns_no_bet_and_zero_stake(self):
        response = self._sport(odds_american=-400)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertTrue(response["no_bets"])

    def test_nba_full_inputs_negative_edge_returns_evaluated_no_bet_status(self):
        response = self._sport(odds_american=-400)
        self.assertLess(response["edge"], 0)
        self.assertEqual(response["logbook_ready_row"]["status"], "evaluated_no_bet")
        self.assertEqual(response["manual_ticket_preview"]["status"], "evaluated_no_bet")
        self.assertEqual(response["no_bets"], [{"reason": "negative edge"}])

    def test_nba_full_inputs_negative_edge_has_no_manual_review_required(self):
        response = self._sport(odds_american=-400)
        self.assertEqual(response["missing_inputs"], [])
        self.assertFalse(response["full_board_preview"]["manual_review_required"])

    def test_nba_missing_inputs_still_returns_manual_review_required_status(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertTrue(response["missing_inputs"])
        self.assertEqual(response["logbook_ready_row"]["status"], "manual_review_required")
        self.assertEqual(response["manual_ticket_preview"]["status"], "manual_review_required")

    def test_nba_positive_edge_below_threshold_returns_edge_too_small_status(self):
        response = self._sport(odds_american=-300)
        self.assertGreater(response["edge"], 0)
        self.assertLess(response["edge"], 2.5)
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["logbook_ready_row"]["status"], "evaluated_no_bet_edge_too_small")
        self.assertEqual(response["no_bets"], [{"reason": "edge too small"}])

    def test_nba_positive_edge_only_confirms_if_confidence_threshold_passes(self):
        strong = self._sport()
        self.assertGreaterEqual(strong["edge"], 2.5)
        self.assertGreaterEqual(strong["confidence"], 70)
        self.assertTrue(strong["confirmed_bets"])
        self.assertGreater(strong["suggested_stake"], 0)

        low_confidence = self._sport(input_stats=nba_full_inputs(
            home_away="neutral",
            key_player_usage_available=False,
            minutes_projection_available=False,
            injury_report_status="questionable",
        ))
        if low_confidence["edge"] and low_confidence["edge"] >= 2.5:
            self.assertLess(low_confidence["confidence"], 70)
        self.assertEqual(low_confidence["confirmed_bets"], [])
        self.assertEqual(low_confidence["suggested_stake"], 0)

    def test_nba_confirmed_bet_requires_all_bet_rules_to_pass(self):
        strong = self._sport()
        self.assertGreaterEqual(strong["edge"], 2.5)
        self.assertGreaterEqual(strong["confidence"], 70)
        self.assertNotIn("negative edge", strong["no_bet_flags"])
        self.assertNotIn("edge too small", strong["no_bet_flags"])
        self.assertNotIn("low confidence", strong["no_bet_flags"])
        self.assertTrue(strong["confirmed_bets"])
        self.assertEqual(strong["logbook_ready_row"]["status"], "confirmed_bet")

        negative_edge = self._sport(odds_american=-400)
        self.assertEqual(negative_edge["confirmed_bets"], [])
        self.assertEqual(negative_edge["logbook_ready_row"]["status"], "evaluated_no_bet")

        low_confidence = self._sport(input_stats=nba_full_inputs(
            home_away="neutral",
            key_player_usage_available=False,
            minutes_projection_available=False,
            injury_report_status="questionable",
        ))
        self.assertEqual(low_confidence["confirmed_bets"], [])
        if "low confidence" in low_confidence["no_bet_flags"]:
            self.assertEqual(low_confidence["logbook_ready_row"]["status"], "evaluated_no_bet_low_confidence")

    def test_nba_plus_100_confirmed_bet_has_no_contradictory_no_bets_entry(self):
        response = self._screenshot(
            event="Nuggets at Lakers",
            teams=["Nuggets", "Lakers"],
            selection="Lakers",
            odds_american=100,
            bankroll=500,
            input_stats=nba_lakers_balanced_inputs(),
        )
        self.assertEqual(response["logbook_ready_rows"][0]["status"], "confirmed_bet")
        self.assertEqual(response["logbook_ready_rows"][0]["decision"], "CONFIRMED_BET")
        self.assertEqual(response["logbook_ready_rows"][0]["stake"], 8.8)
        self.assertFalse(any(
            no_bet.get("reason") == "confirmed bet rules not satisfied"
            for no_bet in response["full_board_preview"]["no_bets"]
        ))

    def test_nba_plus_100_confirmed_bet_keeps_confirmed_bets_populated(self):
        response = self._screenshot(
            event="Nuggets at Lakers",
            teams=["Nuggets", "Lakers"],
            selection="Lakers",
            odds_american=100,
            bankroll=500,
            input_stats=nba_lakers_balanced_inputs(),
        )
        self.assertTrue(response["full_board_preview"]["confirmed_bets"])
        confirmed = response["full_board_preview"]["confirmed_bets"][0]
        self.assertEqual(confirmed["selection"], "Lakers")
        self.assertEqual(confirmed["market"], "moneyline")

    def test_nba_minus_120_negative_edge_keeps_no_bets_and_no_confirmed_bets(self):
        response = self._sport(
            event_id="Nuggets at Lakers",
            selection="Lakers",
            odds_american=-120,
            bankroll=500,
            input_stats=nba_lakers_balanced_inputs(),
        )
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["no_bets"], [{"reason": "negative edge"}])
        self.assertEqual(response["logbook_ready_row"]["status"], "evaluated_no_bet")
        self.assertFalse(response["full_board_preview"]["manual_review_required"])

    def test_full_board_preview_never_returns_confirmed_and_no_bet_for_same_selection(self):
        confirmed = {
            "sport": "basketball_nba",
            "event": "Nuggets at Lakers",
            "market": "moneyline",
            "selection": "Lakers",
        }
        board = build_full_board_preview(
            ticket={"sport": "basketball_nba", "event": "Nuggets at Lakers", "market": "moneyline", "selection": "Lakers"},
            model_analysis={
                "confirmed_bets": [confirmed],
                "full_board_preview": {
                    "confirmed_bets": [confirmed],
                    "no_bets": [
                        {
                            "sport": "basketball_nba",
                            "event": "Nuggets at Lakers",
                            "market": "moneyline",
                            "selection": "Lakers",
                            "reason": "confirmed bet rules not satisfied",
                        },
                        {
                            "sport": "basketball_nba",
                            "event": "Nuggets at Lakers",
                            "market": "spread",
                            "selection": "Lakers -4.5",
                            "reason": "separate market warning",
                        },
                    ],
                },
            },
            provider_enrichment={"odds_provider": {"provider_status": "available"}},
        )
        confirmed_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in board["confirmed_bets"]
        }
        no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in board["no_bets"]
        }
        self.assertFalse(confirmed_keys & no_bet_keys)
        self.assertEqual(board["no_bets"], [{
            "sport": "basketball_nba",
            "event": "Nuggets at Lakers",
            "market": "spread",
            "selection": "Lakers -4.5",
            "reason": "separate market warning",
        }])

    def test_screenshot_analysis_passes_nba_full_inputs_to_sport_model(self):
        response = self._screenshot()
        self.assertTrue(response["ok"])
        self.assertFalse(response["partial_model_mode"])
        self.assertEqual(response["missing_inputs"], [])
        self.assertIsNotNone(response["model_analysis"]["estimated_true_probability"])
        self.assertIsNotNone(response["model_analysis"]["edge"])
        self.assertTrue(response["logbook_ready_rows"])

    def test_no_nba_screenshot_input_creates_no_500(self):
        app.dependency_overrides[require_action_key] = lambda: None
        client = TestClient(app)
        response = client.post("/api/actions/ticket/screenshot-analysis", json={"sport": "nba"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["partial_model_mode"])
        self.assertEqual(body["confirmed_bets"], [])
