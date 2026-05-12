import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from main import AnalyzeEventRequest, AnalyzeEventResponse


class TestAnalyzeEvent(unittest.TestCase):
    def test_analyze_event_request_model_validation(self):
        """Test that AnalyzeEventRequest can be instantiated with valid data."""
        request = AnalyzeEventRequest(
            sport="baseball_mlb",
            league="baseball_mlb",
            event_id="test-event-123",
            markets="h2h,spreads,totals",
            provider=None,
            bankroll=1000,
            unit_size=25,
            risk_profile="conservative",
            max_stake_pct=0.02,
            independent_inputs=None
        )

        self.assertEqual(request.sport, "baseball_mlb")
        self.assertEqual(request.league, "baseball_mlb")
        self.assertEqual(request.event_id, "test-event-123")
        self.assertEqual(request.markets, "h2h,spreads,totals")
        self.assertEqual(request.bankroll, 1000)
        self.assertEqual(request.unit_size, 25)
        self.assertEqual(request.risk_profile, "conservative")
        self.assertEqual(request.max_stake_pct, 0.02)
        self.assertIsNone(request.provider)
        self.assertIsNone(request.independent_inputs)

    def test_analyze_event_request_with_independent_inputs(self):
        """Test AnalyzeEventRequest with independent inputs provided."""
        independent_inputs = {
            "projection_probability": 0.55,
            "pitcher_adjustment": 0.02,
            "weather_adjustment": -0.01
        }

        request = AnalyzeEventRequest(
            sport="basketball_nba",
            league="basketball_nba",
            event_id="test-event-456",
            markets="h2h",
            bankroll=2000,
            unit_size=50,
            risk_profile="standard",
            max_stake_pct=0.05,
            independent_inputs=independent_inputs
        )

        self.assertEqual(request.independent_inputs, independent_inputs)
        self.assertEqual(request.risk_profile, "standard")
        self.assertEqual(request.max_stake_pct, 0.05)

    def test_analyze_event_response_model_structure(self):
        """Test that AnalyzeEventResponse has the correct structure."""
        response = AnalyzeEventResponse(
            ok=True,
            endpoint="analyzeBettingEvent",
            sport="baseball_mlb",
            league="baseball_mlb",
            event_id="test-event-123",
            markets_requested=["h2h", "spreads", "totals"],
            probability_type="blended_market_and_projection"
        )

        self.assertTrue(response.ok)
        self.assertEqual(response.endpoint, "analyzeBettingEvent")
        self.assertEqual(response.sport, "baseball_mlb")
        self.assertEqual(response.league, "baseball_mlb")
        self.assertEqual(response.event_id, "test-event-123")
        self.assertEqual(response.markets_requested, ["h2h", "spreads", "totals"])
        self.assertEqual(response.probability_type, "blended_market_and_projection")
        self.assertEqual(response.confirmed_bets, [])
        self.assertEqual(response.target_lines, [])
        self.assertEqual(response.no_bets, [])
        self.assertEqual(response.warnings, [])
        self.assertIsNone(response.error)
        self.assertIsNone(response.detail)
        self.assertIsNone(response.step_failed)

    def test_analyze_event_endpoint_import(self):
        """Test that the analyze event endpoint can be imported without errors."""
        from main import AnalyzeEventRequest, AnalyzeEventResponse, action_analyze_betting_event

        # Verify the endpoint function exists
        self.assertTrue(callable(action_analyze_betting_event))

        # Verify it's async
        import inspect
        self.assertTrue(inspect.iscoroutinefunction(action_analyze_betting_event))

    def test_analyze_event_request_validation_edge_cases(self):
        """Test AnalyzeEventRequest validation with edge cases."""
        # Test with minimum valid data
        request = AnalyzeEventRequest(
            sport="baseball_mlb",
            league="baseball_mlb",
            event_id="test-event-123"
        )

        self.assertEqual(request.sport, "baseball_mlb")
        self.assertEqual(request.league, "baseball_mlb")
        self.assertEqual(request.event_id, "test-event-123")
        # Check defaults are applied
        self.assertEqual(request.markets, "h2h,spreads,totals")
        self.assertEqual(request.bankroll, 1000)
        self.assertEqual(request.risk_profile, "conservative")

    def test_analyze_event_response_all_fields(self):
        """Test AnalyzeEventResponse with all possible fields populated."""
        response = AnalyzeEventResponse(
            ok=True,
            endpoint="analyzeBettingEvent",
            sport="baseball_mlb",
            league="baseball_mlb",
            event_id="test-event-123",
            markets_requested=["h2h", "spreads"],
            probability_type="market_derived",
            confirmed_bets=[{"decision": "BET", "stake": 25}],
            target_lines=[{"decision": "TARGET", "stake": 0}],
            no_bets=[{"decision": "NO_BET", "reason": "low_edge"}],
            warnings=["Market-derived probabilities only"],
            model_limitations=["Advanced providers missing"],
            missing_inputs=["projection_probability"],
            active_inputs=["market_probability"],
            market_summary=[{"market": "h2h", "best_price": -110}],
            evaluation_results=[{"market": "h2h", "ev": 0.05}],
            log_ready_rows=[{"timestamp": "2023-01-01T00:00:00Z"}],
            error=None,
            detail=None,
            step_failed=None
        )

        self.assertEqual(len(response.confirmed_bets), 1)
        self.assertEqual(len(response.target_lines), 1)
        self.assertEqual(len(response.no_bets), 1)
        self.assertEqual(len(response.warnings), 1)
        self.assertEqual(response.confirmed_bets[0]["decision"], "BET")
        self.assertEqual(response.probability_type, "market_derived")

    def test_analyze_event_validation_incomplete_rows(self):
        """Test that incomplete rows without sportsbook are skipped."""
        from main import action_analyze_betting_event

        # Mock price response with incomplete rows
        mock_price_response = {
            "ok": True,
            "evaluation_ready_lines": [
                {
                    "sportsbook": None,  # Missing sportsbook
                    "market": "h2h",
                    "selection": "Team A",
                    "odds_american": -110
                },
                {
                    "sportsbook": "unknown",  # Invalid sportsbook
                    "market": "h2h",
                    "selection": "Team B",
                    "odds_american": +100
                }
            ]
        }

        # Mock model response
        mock_model_response = {
            "ok": True,
            "final_probability": 0.55,
            "probability_type": "market_derived",
            "model_limitations": [],
            "missing_inputs": [],
            "active_inputs": []
        }

        # Mock evaluate response (should not be called due to validation failure)
        mock_evaluate_response = {"ok": True, "results": []}

        with patch('main.action_fetch_event_odds_envelope') as mock_odds, \
             patch('main.action_price_betting_event', new_callable=AsyncMock) as mock_price, \
             patch('main.action_calculate_model_probability', new_callable=AsyncMock) as mock_model, \
             patch('main.action_evaluate_betting_lines', new_callable=AsyncMock) as mock_evaluate:

            mock_odds.return_value = {"ok": True, "markets": []}
            mock_price.return_value = mock_price_response
            mock_model.return_value = mock_model_response
            mock_evaluate.return_value = mock_evaluate_response

            request = AnalyzeEventRequest(
                sport="baseball_mlb",
                league="baseball_mlb",
                event_id="test-event-123"
            )

            response = asyncio.run(action_analyze_betting_event(request))

            # Should return error due to no valid lines
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"], "no_valid_evaluation_lines")
            self.assertEqual(response["step_failed"], "evaluate_lines")
            self.assertIn("sportsbook was missing", " ".join(response["warnings"]))

    def test_analyze_event_validation_none_odds(self):
        """Test that rows with odds_american None are skipped."""
        from main import action_analyze_betting_event

        mock_price_response = {
            "ok": True,
            "evaluation_ready_lines": [
                {
                    "sportsbook": "draftkings",
                    "market": "h2h",
                    "selection": "Team A",
                    "odds_american": None  # Missing odds
                }
            ]
        }

        mock_model_response = {
            "ok": True,
            "final_probability": 0.55,
            "probability_type": "market_derived",
            "model_limitations": [],
            "missing_inputs": [],
            "active_inputs": []
        }

        with patch('main.action_fetch_event_odds_envelope') as mock_odds, \
             patch('main.action_price_betting_event', new_callable=AsyncMock) as mock_price, \
             patch('main.action_calculate_model_probability', new_callable=AsyncMock) as mock_model, \
             patch('main.action_evaluate_betting_lines', new_callable=AsyncMock) as mock_evaluate:

            mock_odds.return_value = {"ok": True, "markets": []}
            mock_price.return_value = mock_price_response
            mock_model.return_value = mock_model_response
            mock_evaluate.return_value = {"ok": True, "results": []}

            request = AnalyzeEventRequest(
                sport="baseball_mlb",
                league="baseball_mlb",
                event_id="test-event-123"
            )

            response = asyncio.run(action_analyze_betting_event(request))

            # Should return error due to no valid lines
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"], "no_valid_evaluation_lines")
            self.assertIn("odds_american was missing", " ".join(response["warnings"]))

    def test_analyze_event_validation_valid_rows(self):
        """Test that valid rows are passed to evaluateBettingLines."""
        from main import action_analyze_betting_event

        mock_price_response = {
            "ok": True,
            "evaluation_ready_lines": [
                {
                    "sportsbook": "draftkings",
                    "market": "h2h",
                    "selection": "Team A",
                    "odds_american": -110,
                    "line": None,
                    "correlation_group": "h2h_group"
                }
            ]
        }

        mock_model_response = {
            "ok": True,
            "final_probability": 0.55,
            "probability_type": "blended_market_and_projection",
            "model_limitations": [],
            "missing_inputs": [],
            "active_inputs": ["projection_probability"]
        }

        mock_evaluate_response = {
            "ok": True,
            "results": [{
                "market": "h2h",
                "selection": "Team A",
                "decision": "BET",
                "stake": 25,
                "expected_value": 0.05,
                "odds_american": -110
            }]
        }

        with patch('main.action_fetch_event_odds_envelope') as mock_odds, \
             patch('main.action_price_betting_event', new_callable=AsyncMock) as mock_price, \
             patch('main.action_calculate_model_probability', new_callable=AsyncMock) as mock_model, \
             patch('main.action_evaluate_betting_lines', new_callable=AsyncMock) as mock_evaluate:

            mock_odds.return_value = {"ok": True, "markets": []}
            mock_price.return_value = mock_price_response
            mock_model.return_value = mock_model_response
            mock_evaluate.return_value = mock_evaluate_response

            request = AnalyzeEventRequest(
                sport="baseball_mlb",
                league="baseball_mlb",
                event_id="test-event-123"
            )

            response = asyncio.run(action_analyze_betting_event(request))

            # Should succeed with valid lines
            self.assertTrue(response["ok"])
            self.assertEqual(response["probability_type"], "blended_market_and_projection")
            self.assertEqual(len(response["confirmed_bets"]), 1)
            self.assertEqual(response["confirmed_bets"][0]["decision"], "BET")

            # Verify evaluateBettingLines was called with valid lines
            mock_evaluate.assert_called_once()
            call_args = mock_evaluate.call_args[0][0]  # First positional argument (EvaluateLinesRequest)
            self.assertEqual(len(call_args.lines), 1)
            self.assertEqual(call_args.lines[0].sportsbook, "draftkings")
            self.assertEqual(call_args.lines[0].odds_american, -110)

    def test_analyze_event_model_probability_missing(self):
        """Test that missing model_probability doesn't crash the pipeline."""
        from main import action_analyze_betting_event

        mock_price_response = {
            "ok": True,
            "evaluation_ready_lines": [
                {
                    "sportsbook": "draftkings",
                    "market": "h2h",
                    "selection": "Team A",
                    "odds_american": -110
                }
            ]
        }

        # Model response with None final_probability
        mock_model_response = {
            "ok": True,
            "final_probability": None,  # Missing probability
            "probability_type": "market_derived",
            "model_limitations": ["Model probability missing"],
            "missing_inputs": ["projection_probability"],
            "active_inputs": ["market_probability"]
        }

        mock_evaluate_response = {
            "ok": True,
            "results": [{
                "market": "h2h",
                "selection": "Team A",
                "decision": "no_bet_model_missing",  # Expected when model_probability is None
                "stake": 0,
                "expected_value": 0.0
            }]
        }

        with patch('main.action_fetch_event_odds_envelope') as mock_odds, \
             patch('main.action_price_betting_event', new_callable=AsyncMock) as mock_price, \
             patch('main.action_calculate_model_probability', new_callable=AsyncMock) as mock_model, \
             patch('main.action_evaluate_betting_lines', new_callable=AsyncMock) as mock_evaluate:

            mock_odds.return_value = {"ok": True, "markets": []}
            mock_price.return_value = mock_price_response
            mock_model.return_value = mock_model_response
            mock_evaluate.return_value = mock_evaluate_response

            request = AnalyzeEventRequest(
                sport="baseball_mlb",
                league="baseball_mlb",
                event_id="test-event-123"
            )

            response = asyncio.run(action_analyze_betting_event(request))

            # Should succeed but with no bets due to missing model probability
            self.assertTrue(response["ok"])
            self.assertEqual(response["probability_type"], "market_derived")
            self.assertEqual(len(response["confirmed_bets"]), 0)
            self.assertEqual(len(response["no_bets"]), 1)
            self.assertEqual(response["no_bets"][0]["decision"], "no_bet_model_missing")

    def test_analyze_event_request_defaults(self):
        """Test AnalyzeEventRequest with default values."""
        request = AnalyzeEventRequest(
            sport="baseball_mlb",
            league="baseball_mlb",
            event_id="test-event-123"
        )

        # Check default values
        self.assertEqual(request.markets, "h2h,spreads,totals")
        self.assertEqual(request.bankroll, 1000)
        self.assertEqual(request.unit_size, 25)
        self.assertEqual(request.risk_profile, "conservative")
        self.assertEqual(request.max_stake_pct, 0.02)
        self.assertIsNone(request.provider)
        self.assertIsNone(request.independent_inputs)

    def test_analyze_event_response_with_warnings(self):
        """Test AnalyzeEventResponse with warnings and limitations."""
        response = AnalyzeEventResponse(
            ok=True,
            endpoint="analyzeBettingEvent",
            sport="baseball_mlb",
            league="baseball_mlb",
            event_id="test-event-123",
            markets_requested=["h2h"],
            probability_type="market_derived",
            warnings=["Analysis based on market-derived probabilities only"],
            model_limitations=["Advanced providers missing"],
            missing_inputs=["projection_probability"],
            active_inputs=["market_probability"]
        )

        self.assertEqual(response.probability_type, "market_derived")
        self.assertEqual(len(response.warnings), 1)
        self.assertIn("market-derived probabilities", response.warnings[0])
        self.assertEqual(len(response.model_limitations), 1)
        self.assertEqual(response.missing_inputs, ["projection_probability"])
        self.assertEqual(response.active_inputs, ["market_probability"])


if __name__ == "__main__":
    unittest.main()
