import asyncio
import inspect
import unittest
from unittest.mock import AsyncMock, patch

from main import AnalyzeEventRequest, AnalyzeEventResponse


def _line(
    sportsbook="draftkings",
    market="h2h",
    selection="Team A",
    odds_american=-110,
    line=None,
    **extra,
):
    row = {
        "sportsbook": sportsbook,
        "market": market,
        "selection": selection,
        "line": line,
        "odds_american": odds_american,
    }
    row.update(extra)
    return row


def _model_result(row, final_probability=0.55, probability_type="blended_market_and_projection"):
    return {
        "ok": True,
        "final_probability": final_probability,
        "probability_type": probability_type,
        "row": row,
        "model_limitations": [],
        "missing_inputs": [],
        "active_inputs": ["market_probability"],
    }


class TestAnalyzeEvent(unittest.TestCase):
    def _run_analyze(
        self,
        price_response,
        model_response,
        evaluate_response=None,
        request_kwargs=None,
    ):
        from main import action_analyze_betting_event

        evaluate_response = evaluate_response or {"ok": True, "results": []}
        request_kwargs = request_kwargs or {}

        with patch("main.action_fetch_event_odds_envelope") as mock_odds, \
             patch("main.action_price_betting_event", new_callable=AsyncMock) as mock_price, \
             patch("main.action_calculate_model_probability", new_callable=AsyncMock) as mock_model, \
             patch("main.action_evaluate_betting_lines", new_callable=AsyncMock) as mock_evaluate:
            mock_odds.return_value = {"ok": True, "markets": []}
            mock_price.return_value = price_response
            mock_model.return_value = model_response
            mock_evaluate.return_value = evaluate_response

            request = AnalyzeEventRequest(
                sport="baseball_mlb",
                league="baseball_mlb",
                event_id="test-event-123",
                **request_kwargs,
            )
            response = asyncio.run(action_analyze_betting_event(request))

        return response, mock_evaluate

    def test_analyze_event_request_model_validation(self):
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
            independent_inputs=None,
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
        independent_inputs = {
            "projection_probability": 0.55,
            "pitcher_adjustment": 0.02,
            "weather_adjustment": -0.01,
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
            independent_inputs=independent_inputs,
        )

        self.assertEqual(request.independent_inputs, independent_inputs)
        self.assertEqual(request.risk_profile, "standard")
        self.assertEqual(request.max_stake_pct, 0.05)

    def test_analyze_event_response_model_structure(self):
        response = AnalyzeEventResponse(
            ok=True,
            endpoint="analyzeBettingEvent",
            sport="baseball_mlb",
            league="baseball_mlb",
            event_id="test-event-123",
            markets_requested=["h2h", "spreads", "totals"],
            probability_type="blended_market_and_projection",
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
        from main import action_analyze_betting_event

        self.assertTrue(callable(action_analyze_betting_event))
        self.assertTrue(inspect.iscoroutinefunction(action_analyze_betting_event))

    def test_analyze_event_request_validation_edge_cases_and_defaults(self):
        request = AnalyzeEventRequest(
            sport="baseball_mlb",
            league="baseball_mlb",
            event_id="test-event-123",
        )

        self.assertEqual(request.markets, "h2h,spreads,totals")
        self.assertEqual(request.bankroll, 1000)
        self.assertEqual(request.unit_size, 25)
        self.assertEqual(request.risk_profile, "conservative")
        self.assertEqual(request.max_stake_pct, 0.02)
        self.assertIsNone(request.provider)
        self.assertIsNone(request.independent_inputs)

    def test_analyze_event_response_all_fields(self):
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
            step_failed=None,
        )

        self.assertEqual(len(response.confirmed_bets), 1)
        self.assertEqual(len(response.target_lines), 1)
        self.assertEqual(len(response.no_bets), 1)
        self.assertEqual(len(response.warnings), 1)
        self.assertEqual(response.confirmed_bets[0]["decision"], "BET")
        self.assertEqual(response.probability_type, "market_derived")
        self.assertEqual(response.missing_inputs, ["projection_probability"])

    def test_analyze_event_response_with_warnings(self):
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
            active_inputs=["market_probability"],
        )

        self.assertEqual(response.probability_type, "market_derived")
        self.assertIn("market-derived probabilities", response.warnings[0])
        self.assertEqual(response.model_limitations, ["Advanced providers missing"])
        self.assertEqual(response.missing_inputs, ["projection_probability"])
        self.assertEqual(response.active_inputs, ["market_probability"])

    def test_analyze_event_failure_handling_response_shape(self):
        price_response = {
            "ok": False,
            "error": "EVENT_PRICING_FAILED",
            "detail": "pricing failed",
            "market_summary": [{"market": "h2h"}],
        }
        response, mock_evaluate = self._run_analyze(
            price_response=price_response,
            model_response={"ok": True, "results": []},
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["endpoint"], "analyzeBettingEvent")
        self.assertEqual(response["error"], "EVENT_PRICING_FAILED")
        self.assertEqual(response["step_failed"], "price_event")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["target_lines"], [])
        self.assertEqual(response["no_bets"], [])
        self.assertEqual(response["market_summary"], [{"market": "h2h"}])
        mock_evaluate.assert_not_called()

    def test_analyze_event_validation_incomplete_rows(self):
        price_response = {
            "ok": True,
            "evaluation_ready_lines": [
                _line(sportsbook=None),
                _line(sportsbook="unknown", selection="Team B", odds_american=100),
            ],
        }
        model_response = {
            "ok": True,
            "probability_type": "market_derived",
            "results": [],
            "model_limitations": [],
            "missing_inputs": [],
            "active_inputs": [],
        }
        response, mock_evaluate = self._run_analyze(price_response, model_response)

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "no_valid_evaluation_lines")
        self.assertEqual(response["step_failed"], "evaluate_lines")
        self.assertIn("sportsbook was missing", " ".join(response["warnings"]))
        mock_evaluate.assert_not_called()

    def test_analyze_event_validation_none_odds(self):
        price_response = {
            "ok": True,
            "evaluation_ready_lines": [_line(odds_american=None)],
        }
        model_response = {
            "ok": True,
            "probability_type": "market_derived",
            "results": [],
            "model_limitations": [],
            "missing_inputs": [],
            "active_inputs": [],
        }
        response, mock_evaluate = self._run_analyze(price_response, model_response)

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "no_valid_evaluation_lines")
        self.assertIn("odds_american was missing", " ".join(response["warnings"]))
        mock_evaluate.assert_not_called()

    def test_analyze_event_validation_valid_rows(self):
        row = _line(correlation_group="h2h_group")
        price_response = {"ok": True, "evaluation_ready_lines": [row]}
        model_response = {
            "ok": True,
            "results": [_model_result(row, final_probability=0.55)],
        }
        evaluate_response = {
            "ok": True,
            "results": [{
                "market": "h2h",
                "selection": "Team A",
                "decision": "BET",
                "stake": 25,
                "expected_value": 0.05,
                "odds_american": -110,
                "model_probability": 0.55,
            }],
        }

        response, mock_evaluate = self._run_analyze(
            price_response,
            model_response,
            evaluate_response,
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["probability_type"], "blended_market_and_projection")
        self.assertEqual(len(response["confirmed_bets"]), 1)
        self.assertEqual(response["confirmed_bets"][0]["selection"], "Team A")
        self.assertEqual(response["target_lines"], [])
        call_args = mock_evaluate.call_args[0][0]
        self.assertEqual(len(call_args.lines), 1)
        self.assertEqual(call_args.lines[0].sportsbook, "draftkings")
        self.assertEqual(call_args.lines[0].odds_american, -110)
        self.assertEqual(call_args.lines[0].model_probability, 0.55)

    def test_market_derived_uses_no_vig_probability(self):
        row = _line(no_vig_probability=0.61, consensus_probability=0.52, implied_probability=0.51)
        response, mock_evaluate = self._run_market_derived_case(
            [row],
            [{"decision": "NO_BET", "model_probability": 0.61}],
        )

        self.assertTrue(response["ok"])
        self.assertEqual(mock_evaluate.call_args[0][0].lines[0].model_probability, 0.61)

    def test_market_derived_falls_back_to_consensus_probability(self):
        row = _line(consensus_probability=0.57, implied_probability=0.51)
        response, mock_evaluate = self._run_market_derived_case(
            [row],
            [{"decision": "NO_BET", "model_probability": 0.57}],
        )

        self.assertTrue(response["ok"])
        self.assertEqual(mock_evaluate.call_args[0][0].lines[0].model_probability, 0.57)

    def test_market_derived_falls_back_to_implied_probability(self):
        row = _line(implied_probability=0.53)
        response, mock_evaluate = self._run_market_derived_case(
            [row],
            [{"decision": "NO_BET", "model_probability": 0.53}],
        )

        self.assertTrue(response["ok"])
        self.assertEqual(mock_evaluate.call_args[0][0].lines[0].model_probability, 0.53)

    def test_market_derived_strong_bet_is_reclassified_to_target_lines(self):
        row = _line(no_vig_probability=0.64)
        response, _ = self._run_market_derived_case(
            [row],
            [{"decision": "strong_bet", "stake": 25}],
        )

        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(len(response["target_lines"]), 1)
        self.assertEqual(response["target_lines"][0]["decision"], "target_market_derived")
        self.assertTrue(response["target_lines"][0]["market_derived_only"])

    def test_market_derived_bet_is_reclassified_to_target_lines(self):
        row = _line(no_vig_probability=0.62)
        response, _ = self._run_market_derived_case(
            [row],
            [{"decision": "BET", "stake": 25}],
        )

        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(len(response["target_lines"]), 1)
        self.assertEqual(response["target_lines"][0]["decision"], "target_market_derived")
        self.assertTrue(response["target_lines"][0]["market_derived_only"])

    def test_no_market_derived_result_appears_in_confirmed_bets(self):
        rows = [
            _line(selection="Team A", no_vig_probability=0.62),
            _line(sportsbook="fanduel", selection="Team B", odds_american=105, no_vig_probability=0.58),
        ]
        response, _ = self._run_market_derived_case(
            rows,
            [
                {"decision": "BET", "selection": "Team A", "stake": 25},
                {"decision": "strong bet", "selection": "Team B", "stake": 20},
            ],
        )

        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(len(response["target_lines"]), 2)
        self.assertTrue(all(line["market_derived_only"] for line in response["target_lines"]))

    def test_invalid_model_probability_rows_are_skipped_with_warning(self):
        rows = [
            _line(selection="Valid", no_vig_probability=0.55),
            _line(selection="None", no_vig_probability=None),
            _line(selection="Zero", no_vig_probability=0),
            _line(selection="One", no_vig_probability=1),
            _line(selection="Negative", no_vig_probability=-0.1),
            _line(selection="Too High", no_vig_probability=1.1),
        ]
        response, mock_evaluate = self._run_market_derived_case(
            rows,
            [{"decision": "NO_BET", "selection": "Valid"}],
        )

        self.assertTrue(response["ok"])
        self.assertEqual(len(mock_evaluate.call_args[0][0].lines), 1)
        self.assertEqual(mock_evaluate.call_args[0][0].lines[0].selection, "Valid")
        self.assertEqual(
            response["warnings"].count(
                "Skipped line because model_probability was invalid for evaluation."
            ),
            5,
        )

    def test_evaluate_betting_lines_receives_valid_model_probability(self):
        rows = [
            _line(selection="A", no_vig_probability=0.56),
            _line(sportsbook="fanduel", selection="B", odds_american=120, consensus_probability=0.48),
            _line(sportsbook="betmgm", selection="C", odds_american=130, implied_probability=0.45),
        ]
        response, mock_evaluate = self._run_market_derived_case(
            rows,
            [{"decision": "NO_BET"} for _ in rows],
        )

        self.assertTrue(response["ok"])
        probabilities = [line.model_probability for line in mock_evaluate.call_args[0][0].lines]
        self.assertEqual(probabilities, [0.56, 0.48, 0.45])

    def _run_market_derived_case(self, rows, evaluate_results):
        model_rows = [
            _model_result(row, final_probability=0.99, probability_type="market_derived")
            for row in rows
        ]
        price_response = {
            "ok": True,
            "evaluation_ready_lines": rows,
            "market_summary": [{"market": "h2h", "probability": 0.99}],
        }
        model_response = {
            "ok": True,
            "probability_type": "market_derived",
            "results": model_rows,
            "model_limitations": [],
            "missing_inputs": ["projection_probability"],
            "active_inputs": ["market_probability"],
        }
        normalized_results = []
        for index, result in enumerate(evaluate_results):
            normalized = {
                "market": rows[index].get("market"),
                "selection": rows[index].get("selection"),
                "line": rows[index].get("line"),
                "odds_american": rows[index].get("odds_american"),
                "stake": 0,
                "expected_value": 0,
            }
            normalized.update(result)
            normalized_results.append(normalized)

        return self._run_analyze(
            price_response,
            model_response,
            {"ok": True, "results": normalized_results},
        )


if __name__ == "__main__":
    unittest.main()
