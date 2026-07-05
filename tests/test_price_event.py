"""Tests for price-event endpoint and market pricing logic."""
from __future__ import annotations

import unittest

import src.core.market_pricing as market_pricing


class TestMarketPricing(unittest.TestCase):
    def test_group_lines_by_market_point_selection(self):
        flat_odds = [
            {
                "market": "totals",
                "selection": "Over",
                "point": 8.5,
                "price_american": -110,
                "sportsbook": "draftkings"
            },
            {
                "market": "totals", 
                "selection": "Under",
                "point": 8.5,
                "price_american": -110,
                "sportsbook": "fanduel"
            },
            {
                "market": "h2h",
                "selection": "Team A",
                "price_american": +150,
                "sportsbook": "draftkings"
            }
        ]
        
        groups = market_pricing.group_lines_by_market_point_selection(flat_odds)
        
        # Should have 3 groups
        self.assertEqual(len(groups), 3)
        
        # Check totals over group
        totals_over_key = ("totals", 8.5, "over")
        self.assertIn(totals_over_key, groups)
        self.assertEqual(len(groups[totals_over_key]), 1)
        
        # Check h2h group
        h2h_key = ("h2h", None, "team a")
        self.assertIn(h2h_key, groups)
        self.assertEqual(len(groups[h2h_key]), 1)

    def test_calculate_market_group_statistics(self):
        group = [
            {"price_american": -110},
            {"price_american": -105},
            {"price_american": +115}
        ]
        
        stats = market_pricing.calculate_market_group_statistics(group)
        
        self.assertIsNotNone(stats)
        self.assertIsNotNone(stats["best_price"])
        self.assertIsNotNone(stats["worst_price"])
        self.assertGreater(stats["average_implied_probability"], 0)
        self.assertGreater(stats["book_hold"], 0)
        self.assertEqual(stats["sample_size"], 3)

    def test_create_evaluation_ready_lines_no_model(self):
        flat_odds = [
            {
                "market": "totals",
                "selection": "Over",
                "point": 8.5,
                "price_american": -110,
                "sportsbook": "draftkings",
                "event_id": "test123",
                "home_team": "Team A",
                "away_team": "Team B"
            },
            {
                "market": "totals",
                "selection": "Under", 
                "point": 8.5,
                "price_american": -110,
                "sportsbook": "fanduel",
                "event_id": "test123",
                "home_team": "Team A",
                "away_team": "Team B"
            }
        ]
        
        lines = market_pricing.create_evaluation_ready_lines(flat_odds)
        
        self.assertEqual(len(lines), 2)
        
        # Check first line
        line = lines[0]
        self.assertEqual(line["market"], "totals")
        self.assertEqual(line["selection"], "Over")
        self.assertEqual(line["line"], 8.5)
        self.assertEqual(line["odds_american"], -110)
        self.assertEqual(line["market_status"], "market_priced_only")
        self.assertIsNone(line["model_probability"])
        self.assertIsNotNone(line["correlation_group"])

    def test_create_evaluation_ready_lines_with_model(self):
        flat_odds = [
            {
                "market": "totals",
                "selection": "Over",
                "point": 8.5,
                "price_american": -110,
                "sportsbook": "draftkings",
                "event_id": "test123",
                "home_team": "Team A",
                "away_team": "Team B"
            }
        ]
        
        model_probs = {
            "totals_8.5": {
                "over": 0.55,
                "under": 0.45
            }
        }
        
        lines = market_pricing.create_evaluation_ready_lines(flat_odds, model_probs)
        
        self.assertEqual(len(lines), 1)
        
        line = lines[0]
        self.assertEqual(line["market_status"], "model_enhanced")
        self.assertEqual(line["model_probability"], 0.55)

    def test_create_market_summary(self):
        evaluation_lines = [
            {
                "market": "totals",
                "line": 8.5,
                "selection": "Over",
                "best_price_in_market": -105,
                "worst_price_in_market": -115,
                "consensus_probability": 0.52,
                "fair_odds_american": -108
            },
            {
                "market": "totals",
                "line": 8.5,
                "selection": "Under",
                "best_price_in_market": -105,
                "worst_price_in_market": -115,
                "consensus_probability": 0.48,
                "fair_odds_american": -108
            }
        ]
        
        summary = market_pricing.create_market_summary(evaluation_lines)
        
        self.assertEqual(len(summary), 1)
        
        market_summary = summary[0]
        self.assertEqual(market_summary["market"], "totals")
        self.assertEqual(market_summary["line"], 8.5)
        self.assertEqual(len(market_summary["selections"]), 2)


class TestPriceEventEndpoint(unittest.TestCase):
    def test_price_event_request_model_validation(self):
        """Test that PriceEventRequest can be instantiated with valid data."""
        from tests.support.action_imports import PriceEventRequest
        
        # Basic request
        request = PriceEventRequest(
            sport="baseball_mlb",
            event_id="test123",
            league="baseball_mlb"
        )
        
        self.assertEqual(request.sport, "baseball_mlb")
        self.assertEqual(request.event_id, "test123")
        self.assertEqual(request.league, "baseball_mlb")
        self.assertEqual(request.markets, "h2h,spreads,totals")
        self.assertEqual(request.bankroll, 1000)
        self.assertEqual(request.unit_size, 25)
        self.assertEqual(request.risk_profile, "conservative")
        self.assertIsNone(request.provider)
        self.assertIsNone(request.model_probabilities)
        
        # Request with model probabilities
        model_probs = {
            "totals_8.5": {"over": 0.55, "under": 0.45},
            "h2h": {"team a": 0.6, "team b": 0.4}
        }
        
        request_with_model = PriceEventRequest(
            sport="baseball_mlb",
            event_id="test123",
            league="baseball_mlb",
            model_probabilities=model_probs
        )
        
        self.assertEqual(request_with_model.model_probabilities, model_probs)


if __name__ == "__main__":
    unittest.main()
