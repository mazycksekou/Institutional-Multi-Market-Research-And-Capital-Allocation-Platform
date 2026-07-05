import asyncio
import unittest
from copy import deepcopy

import src.market_intelligence.multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "formula_e_energy_management_attack_mode_street_circuit_monte_carlo_model"


def formula_e_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("formula_e")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def formula_e_inputs(**extra):
    payload = registry.get_sport_model_config("formula_e")["screenshot_alias_test_payload"]
    normalized = registry.normalize_sport_inputs_for_model(
        sport=payload["sport"],
        market=payload["market"],
        selection=payload["selection"],
        input_stats=payload["input_stats"],
        ticket=payload,
    )["input_stats"]
    normalized.update(extra)
    return normalized


def payload(**extra):
    data = {
        "sport": "formula_e",
        "league": "Formula E",
        "event_id": "Monaco E-Prix",
        "event": "Monaco E-Prix",
        "market": "race_head_to_head",
        "selection": "Jake Dennis",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Jake Dennis race head to head +100 vs Pascal Wehrlein",
        "visible_markets": ["race_head_to_head"],
        "input_stats": formula_e_inputs(),
    }
    data.update(extra)
    return data


class TestFormulaEModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "fe",
            "league": "Formula E",
            "event": "Monaco E-Prix",
            "market": "race_head_to_head",
            "selection": "Jake Dennis",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Jake Dennis race head to head +100 vs Pascal Wehrlein",
            "visible_markets": ["race_head_to_head"],
            "input_stats": formula_e_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "formula_e")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("formula_e")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "formula_e_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_formula_e_model(self):
        for alias in ("formula_e", "formulae", "fe", "fia_formula_e", "abb_formula_e", "electric_racing", "motorsport_formula_e"):
            self.assertEqual(registry.normalize_sport_key(alias), "formula_e")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self): self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = formula_e_alias_inputs()
        for key in ("driver_power_rating", "energy_rating", "attack_eff", "regen", "grid_pos"):
            malformed[key] = "bad text"
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertNotEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["confirmed_bets"], [])

    def test_odds_stability_at_three_prices(self):
        results = {odds: self._sport(odds_american=odds) for odds in (-130, 100, 120)}
        probs = [result["final_probability"] for result in results.values()]
        self.assertLess(max(probs) - min(probs), 0.03)
        self.assertLess(results[-130]["edge_percent"], results[100]["edge_percent"])
        self.assertLess(results[100]["edge_percent"], results[120]["edge_percent"])

    def test_negative_edge_creates_no_bet(self): self.assertEqual(self._sport(odds_american=-2000)["status"], "evaluated_no_bet")

    def test_low_confidence_creates_no_bet(self):
        response = self._sport(input_stats=formula_e_inputs(book_count=1, rain_probability=0.70, weather_risk=0.70, dnf_risk=0.24, incident_risk=0.24, qualifying_report_quality="low"))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_social_public_data_alone_cannot_confirm(self):
        response = self._sport(input_stats={"social_sentiment": 90, "public_betting_percent": 75, "sharp_money_percent": 65})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_race_winner_market_works(self): self.assert_active(self._sport(market="race_winner"))
    def test_podium_market_works(self): self.assert_active(self._sport(market="podium_finish"))
    def test_top_5_market_works(self): self.assert_active(self._sport(market="top_5_finish"))
    def test_top_10_market_works(self): self.assert_active(self._sport(market="top_10_finish"))
    def test_points_finish_market_works(self): self.assert_active(self._sport(market="points_finish"))
    def test_qualifying_winner_market_works(self): self.assert_active(self._sport(market="qualifying_winner"))
    def test_qualifying_head_to_head_market_works(self): self.assert_active(self._sport(market="qualifying_head_to_head"))
    def test_race_head_to_head_market_works(self): self.assert_active(self._sport(market="race_head_to_head"))
    def test_fastest_lap_market_works(self): self.assert_active(self._sport(market="fastest_lap"))
    def test_safety_car_market_works(self): self.assert_active(self._sport(market="safety_car", selection="yes"))
    def test_classified_finish_market_works(self): self.assert_active(self._sport(market="classified_finish"))
    def test_finishing_position_market_works(self): self.assert_active(self._sport(market="finishing_position", selection="under", input_stats=formula_e_inputs(line=6.5)))

    def test_street_circuit_calibration_works(self):
        self.assertEqual(self._sport()["circuit_calibration_applied"], "street")

    def test_wet_weather_calibration_works(self):
        self.assertEqual(self._sport(input_stats=formula_e_inputs(rain_probability=0.65, weather_risk=0.65))["event_environment_calibration_applied"], "wet")

    def test_dry_weather_calibration_works(self):
        self.assertEqual(self._sport()["event_environment_calibration_applied"], "dry")

    def test_qualifying_calibration_works(self):
        self.assertTrue(self._sport(market="qualifying_winner")["qualifying_calibration_applied"])

    def test_energy_management_calibration_works(self):
        self.assertTrue(self._sport()["energy_management_calibration_applied"])

    def test_attack_mode_fields_affect_output(self):
        base = self._sport()["formula_e_attack_mode_edge_score"]
        changed = self._sport(input_stats=formula_e_inputs(attack_mode_efficiency=0.70))["formula_e_attack_mode_edge_score"]
        self.assertNotEqual(base, changed)

    def test_battery_regen_fields_affect_output(self):
        base = self._sport()["formula_e_energy_edge_score"]
        changed = self._sport(input_stats=formula_e_inputs(regen_efficiency=0.70, battery_temperature_risk=0.26))["formula_e_energy_edge_score"]
        self.assertNotEqual(base, changed)

    def test_dnf_incident_risk_can_force_no_bet(self):
        response = self._sport(input_stats=formula_e_inputs(dnf_risk=0.36, incident_risk=0.36))
        self.assertIn("dnf incident risk", response["no_bet_flags"])
        self.assertEqual(response["confirmed_bets"], [])

    def test_grid_penalty_affects_output(self):
        base = self._sport()["formula_e_driver_edge_score"]
        changed = self._sport(input_stats=formula_e_inputs(grid_penalty=4))["formula_e_driver_edge_score"]
        self.assertNotEqual(base, changed)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_formula_e_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("formula_e_input_contract", response)
        self.assertIsNotNone(response["formula_e_matchup_probability"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "circuit_calibration_applied", "event_environment_calibration_applied", "qualifying_calibration_applied", "energy_management_calibration_applied"):
            self.assertIn(field, row)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("formula_e")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
