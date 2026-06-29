import unittest

import multi_sport_model_registry as registry
from src.automation_scheduler_legacy.model_recheck_runner import run_model_recheck


class TestModelRecheckRunner(unittest.TestCase):
    def test_missing_inputs_are_skipped(self):
        result = run_model_recheck({"sport": "darts", "market": "moneyline", "selection": "Player A", "input_stats": {}})
        self.assertEqual(result["status"], "skipped_missing_inputs")
        self.assertEqual(result["confirmed_bets"], [])

    def test_valid_local_model_recheck_runs(self):
        ticket = registry.get_sport_model_config("darts")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(
            sport=ticket["sport"],
            market=ticket["market"],
            selection=ticket["selection"],
            input_stats=ticket["input_stats"],
            ticket=ticket,
        )
        result = run_model_recheck(
            {
                "sport": "darts",
                "market": ticket["market"],
                "selection": ticket["selection"],
                "event_id": ticket["event"],
                "odds_american": ticket["odds_american"],
                "input_stats": normalized["input_stats"],
            }
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["model_name"], "darts_checkout_scoring_pressure_leg_set_monte_carlo_model")

    def test_malformed_numeric_inputs_do_not_activate(self):
        ticket = registry.get_sport_model_config("darts")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(
            sport=ticket["sport"],
            market=ticket["market"],
            selection=ticket["selection"],
            input_stats=ticket["input_stats"],
            ticket=ticket,
        )
        normalized["input_stats"]["player_three_dart_average"] = "not-a-number"
        result = run_model_recheck(
            {
                "sport": "darts",
                "market": ticket["market"],
                "selection": ticket["selection"],
                "event_id": ticket["event"],
                "odds_american": ticket["odds_american"],
                "input_stats": normalized["input_stats"],
            }
        )
        self.assertNotEqual(result["model_status"], "active")
        self.assertEqual(result["confirmed_bets"], [])

    def test_enrichment_only_inputs_cannot_confirm(self):
        result = run_model_recheck(
            {
                "sport": "darts",
                "market": "moneyline",
                "selection": "Player A",
                "input_stats": {
                    "public_betting_percent": 80,
                    "sharp_money_percent": 60,
                    "market_movement": 5,
                },
            }
        )
        self.assertEqual(result["status"], "skipped_missing_inputs")
