"""Lightweight tests for evaluate-lines quant path."""
from __future__ import annotations

import unittest

import bet_decision_engine
from quant_engine import american_to_decimal, no_vig_probabilities_two_way


class TestQuantPrimitives(unittest.TestCase):
    def test_american_decimal_round_trip(self):
        self.assertAlmostEqual(american_to_decimal(-110), 1.909090909, places=5)

    def test_two_way_no_vig(self):
        a, b = no_vig_probabilities_two_way(0.55, 0.55)
        self.assertAlmostEqual(a + b, 1.0, places=6)


class TestEvaluateLines(unittest.TestCase):
    def test_missing_model_no_bet(self):
        body = {
            "sport": "baseball_mlb",
            "event": "Test",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "conservative",
            "lines": [
                {
                    "sportsbook": "draftkings",
                    "market": "totals",
                    "selection": "Under",
                    "line": 8.5,
                    "odds_american": -110,
                    "correlation_group": "g1",
                }
            ],
        }
        out = bet_decision_engine.evaluate_lines_payload(body)
        self.assertTrue(out["ok"])
        self.assertEqual(len(out["results"]), 1)
        self.assertEqual(out["results"][0]["decision"], "no_bet_model_missing")
        self.assertEqual(out["results"][0]["suggested_stake"], 0)

    def test_two_way_no_vig_and_model(self):
        body = {
            "sport": "baseball_mlb",
            "event": "Test",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "standard",
            "lines": [
                {
                    "sportsbook": "a",
                    "market": "totals",
                    "selection": "Over",
                    "line": 8.5,
                    "odds_american": -110,
                    "model_probability": 0.55,
                },
                {
                    "sportsbook": "b",
                    "market": "totals",
                    "selection": "Under",
                    "line": 8.5,
                    "odds_american": -110,
                    "model_probability": 0.48,
                },
            ],
        }
        out = bet_decision_engine.evaluate_lines_payload(body)
        self.assertTrue(out["ok"])
        nv0 = out["results"][0]["no_vig_probability"]
        self.assertIsNotNone(nv0)
        self.assertAlmostEqual(nv0, 0.5, places=5)


if __name__ == "__main__":
    unittest.main()
