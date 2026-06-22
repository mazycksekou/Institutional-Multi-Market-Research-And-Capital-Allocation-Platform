import asyncio
import os
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from tests.support.action_imports import ScreenshotAnalysisRequest, action_analyze_ticket_screenshot, app, require_action_key
from providers.kalshi_provider import normalize_kalshi_probability_market


ClientResponseError = type("ClientResponseError", (Exception,), {})


def _payload(**extra):
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
        "risk_profile": "conservative",
        "visible_markets": ["moneyline"],
        "input_stats": {},
    }
    payload.update(extra)
    return payload


class TestScreenshotAnalysis(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def _run(self, payload):
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))

    @patch.dict(os.environ, {}, clear=True)
    def test_screenshot_parsed_ticket_input(self):
        response = self._run(_payload())
        self.assertTrue(response["ok"])
        self.assertEqual(response["endpoint"], "ticketScreenshotAnalysis")
        self.assertEqual(response["parsed_ticket"]["sport"], "basketball_nba")
        self.assertEqual(response["parsed_ticket"]["market"], "moneyline")
        self.assertEqual(response["confirmed_bets"], [])

    @patch.dict(os.environ, {}, clear=True)
    def test_sharp_api_unavailable(self):
        response = self._run(_payload())
        self.assertEqual(response["provider_enrichment"]["sharp"]["provider_status"], "disabled")

    @patch.dict(os.environ, {"SHARP_API_KEY": "key", "SHARP_API_BASE_URL": "https://sharp.example"}, clear=True)
    def test_sharp_api_error(self):
        response = self._run(_payload())
        self.assertEqual(response["provider_enrichment"]["sharp"]["provider_status"], "disabled")
        self.assertEqual(
            response["provider_enrichment"]["sharp"]["provider_notes"],
            [
                "Sharp live odds access has been retired in favor of the connector boundary.",
                "Legacy compatibility shell returns metadata only.",
            ],
        )
        self.assertEqual(response["confirmed_bets"], [])

    @patch.dict(os.environ, {}, clear=True)
    def test_kalshi_unavailable(self):
        response = self._run(_payload())
        self.assertEqual(response["provider_enrichment"]["kalshi"]["provider_status"], "unavailable")

    @patch.dict(os.environ, {"KALSHI_ENABLED": "true", "KALSHI_BASE_URL": "https://kalshi.example"}, clear=True)
    @patch("providers.kalshi_provider.requests.get")
    def test_kalshi_error(self, mock_get):
        mock_get.side_effect = RuntimeError("boom")
        response = self._run(_payload())
        self.assertEqual(response["provider_enrichment"]["kalshi"]["provider_status"], "error")
        self.assertEqual(
            response["provider_enrichment"]["kalshi"]["provider_notes"],
            ["Kalshi provider failed but analysis continued"],
        )
        self.assertEqual(response["confirmed_bets"], [])

    def test_kalshi_probability_normalization(self):
        market = normalize_kalshi_probability_market({
            "ticker": "KXTEST",
            "yes_bid": 48,
            "yes_ask": 52,
            "no_bid": 47,
            "no_ask": 53,
            "liquidity": 1000,
            "volume": 250,
        })
        self.assertEqual(market["market_type"], "kalshi_prediction_market")
        self.assertAlmostEqual(market["yes_bid"], 0.48)
        self.assertAlmostEqual(market["yes_ask"], 0.52)
        self.assertAlmostEqual(market["mid_probability"], 0.50)
        self.assertEqual(market["liquidity"], 1000)
        self.assertEqual(market["volume"], 250)

    @patch.dict(os.environ, {}, clear=True)
    def test_partial_model_mode_and_missing_inputs(self):
        response = self._run(_payload(selection=None, odds_american=None, event=None, teams=[]))
        self.assertTrue(response["partial_model_mode"])
        self.assertIn("selection", response["missing_inputs"])
        self.assertIn("odds_american", response["missing_inputs"])
        self.assertIn("event_or_teams", response["missing_inputs"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_sport_routes_for_requested_sports(self):
        cases = [
            ("nba", "basketball_nba"),
            ("nfl", "americanfootball_nfl"),
            ("mlb", "baseball_mlb"),
            ("nhl", "icehockey_nhl"),
            ("soccer", "soccer"),
            ("boxing", "boxing"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                response = self._run(_payload(sport=raw, league=raw))
                self.assertEqual(response["parsed_ticket"]["sport"], expected)
                self.assertEqual(response["confirmed_bets"], [])

    @patch.dict(os.environ, {}, clear=True)
    def test_full_board_preview_shape_and_visible_only_message(self):
        response = self._run(_payload(visible_props=["Jayson Tatum points"], visible_alt_lines=["Celtics -3.5"]))
        board = response["full_board_preview"]
        for key in [
            "confirmed_bets",
            "target_lines",
            "target_props",
            "target_alt_lines",
            "no_bets",
            "best_correlated_parlay",
            "value_ranking",
            "risk_ranking",
            "missing_inputs",
            "manual_review_required",
            "logbook_ready_rows",
        ]:
            self.assertIn(key, board)
        self.assertTrue(any("Only visible markets" in str(item) for item in board["manual_review_required"]))

    def test_route_no_500_on_incomplete_screenshot_data(self):
        app.dependency_overrides[require_action_key] = lambda: None
        client = TestClient(app)
        response = client.post("/api/actions/ticket/screenshot-analysis", json={"source_type": "chatgpt_parsed"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["partial_model_mode"])
        self.assertEqual(body["confirmed_bets"], [])
        self.assertEqual(body["suggested_stake"], 0)

    @patch.dict(os.environ, {"KALSHI_ENABLED": "true", "KALSHI_BASE_URL": "https://kalshi.example"}, clear=True)
    @patch("providers.kalshi_provider.requests.get")
    def test_no_confirmed_bet_from_provider_data_alone(self, mock_get):
        fake_response = Mock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = {"markets": [{"ticker": "KXTEST", "yes_bid": 48, "yes_ask": 52}]}
        mock_get.return_value = fake_response
        response = self._run(_payload())
        self.assertEqual(response["provider_enrichment"]["kalshi"]["provider_status"], "available")
        self.assertEqual(response["confirmed_bets"], [])

    @patch.dict(os.environ, {"SHARP_API_KEY": "key", "SHARP_API_BASE_URL": "https://sharp.example"}, clear=True)
    def test_sharp_client_response_error_still_returns_ok_true(self):
        response = self._run(_payload())
        self.assertTrue(response["ok"])
        self.assertTrue(response["partial_model_mode"])
        self.assertNotIn("error", response)
        self.assertEqual(response["provider_enrichment"]["sharp"]["provider_status"], "disabled")
        self.assertEqual(
            response["provider_enrichment"]["sharp"]["provider_notes"],
            [
                "Sharp live odds access has been retired in favor of the connector boundary.",
                "Legacy compatibility shell returns metadata only.",
            ],
        )
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertIsNotNone(response["implied_probability"])
        self.assertTrue(response["missing_inputs"])
        self.assertTrue(response["no_bets"])
        self.assertTrue(response["logbook_ready_rows"])

    @patch.dict(os.environ, {"KALSHI_ENABLED": "true", "KALSHI_BASE_URL": "https://kalshi.example"}, clear=True)
    @patch("providers.kalshi_provider.requests.get")
    def test_kalshi_client_response_error_still_returns_ok_true(self, mock_get):
        mock_get.side_effect = ClientResponseError("kalshi failed")
        response = self._run(_payload())
        self.assertTrue(response["ok"])
        self.assertTrue(response["partial_model_mode"])
        self.assertNotIn("error", response)
        self.assertEqual(response["provider_enrichment"]["kalshi"]["provider_status"], "error")
        self.assertEqual(
            response["provider_enrichment"]["kalshi"]["provider_notes"],
            ["Kalshi provider failed but analysis continued"],
        )
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertIsNotNone(response["implied_probability"])
        self.assertTrue(response["missing_inputs"])
        self.assertTrue(response["no_bets"])
        self.assertTrue(response["logbook_ready_rows"])

    @patch.dict(
        os.environ,
        {
            "SHARP_API_KEY": "key",
            "SHARP_API_BASE_URL": "https://sharp.example",
            "KALSHI_ENABLED": "true",
            "KALSHI_BASE_URL": "https://kalshi.example",
        },
        clear=True,
    )
    def test_provider_error_does_not_stop_screenshot_analysis(self):
        response = self._run(_payload())
        self.assertTrue(response["ok"])
        self.assertTrue(response["partial_model_mode"])
        self.assertNotIn("error", response)
        self.assertEqual(response["provider_enrichment"]["sharp"]["provider_status"], "disabled")
        self.assertEqual(response["provider_enrichment"]["kalshi"]["provider_status"], "error")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_top_level_error_only_appears_when_route_itself_fails(self):
        with patch("main.screenshot_intake.analyze_screenshot_ticket", side_effect=RuntimeError("route failed")):
            response = self._run(_payload())
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "screenshot_analysis_failed")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    @patch.dict(os.environ, {"SHARP_API_KEY": "key", "SHARP_API_BASE_URL": "https://sharp.example"}, clear=True)
    def test_no_confirmed_bet_from_provider_failure_or_missing_data(self):
        response = self._run(_payload(selection=None, odds_american=None, event=None, teams=[]))
        self.assertTrue(response["ok"])
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)
        self.assertTrue(response["missing_inputs"])
