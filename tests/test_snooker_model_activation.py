import asyncio
import unittest
from copy import deepcopy

import src.market_intelligence.multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


MODEL_NAME = "snooker_frame_break_safety_potting_monte_carlo_model"
ALIASES = ("snooker", "billiards", "pool", "cue_sports", "world_snooker", "wst", "nine_ball", "eight_ball", "ten_ball", "professional_snooker")


def snooker_alias_inputs(**extra):
    data = deepcopy(registry.get_sport_model_config("snooker")["screenshot_alias_test_payload"]["input_stats"])
    data.update(extra)
    return data


def snooker_inputs(**extra):
    ticket = registry.get_sport_model_config("snooker")["screenshot_alias_test_payload"]
    normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)["input_stats"]
    normalized.update(extra)
    return normalized


def payload(**extra):
    data = {
        "sport": "snooker",
        "league": "WST",
        "event_id": "Judd Trump vs Ronnie O'Sullivan",
        "event": "Judd Trump vs Ronnie O'Sullivan",
        "market": "match_winner",
        "selection": "Judd Trump",
        "odds_american": 100,
        "book": "Manual",
        "bankroll": 1000,
        "unit_size": 25,
        "risk_profile": "moderate",
        "source_type": "unit_test",
        "screenshot_text": "Judd Trump match winner +100 vs Ronnie O'Sullivan",
        "visible_markets": ["match_winner", "frame_handicap", "player_total_centuries"],
        "input_stats": snooker_inputs(),
    }
    data.update(extra)
    return data


class TestSnookerModelActivation(unittest.TestCase):
    def _sport(self, **extra):
        return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload(**extra))))

    def _screenshot(self, **extra):
        data = {
            "source_type": "chatgpt_parsed",
            "sport": "world_snooker",
            "league": "WST",
            "event": "Judd Trump vs Ronnie O'Sullivan",
            "market": "match_winner",
            "selection": "Judd Trump",
            "odds_american": 100,
            "book": "Manual",
            "bankroll": 1000,
            "unit_size": 25,
            "risk_profile": "moderate",
            "screenshot_text": "Judd Trump match winner +100 vs Ronnie O'Sullivan",
            "visible_markets": ["match_winner", "frame_handicap", "player_total_centuries"],
            "input_stats": snooker_alias_inputs(),
        }
        data.update(extra)
        return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**data)))

    def assert_active(self, response):
        self.assertEqual(response["model_name"], MODEL_NAME)
        self.assertEqual(response["model_status"], "active")
        self.assertEqual(response["league_calibration_applied"], "snooker")
        self.assertIsNotNone(response["final_probability"])

    def test_registry_entry_exists(self):
        config = registry.get_sport_model_config("snooker")
        self.assertTrue(config["confirmed_bets_allowed"])
        self.assertEqual(config["model_used"], MODEL_NAME)
        self.assertEqual(config["input_normalizer"], "snooker_input_normalizer")
        self.assertTrue(config["screenshot_alias_test_payload"])

    def test_aliases_route_to_snooker_model(self):
        for alias in ALIASES:
            self.assertEqual(registry.normalize_sport_key(alias), "snooker")
            self.assertEqual(registry.get_sport_model_config(alias)["model_used"], MODEL_NAME)

    def test_active_payload_confirms_model_active(self):
        self.assert_active(self._sport())

    def test_missing_inputs_returns_inactive_missing_data(self):
        response = self._sport(input_stats={})
        self.assertEqual(response["model_status"], "inactive_missing_data")
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_missing_single_required_field_blocks_activation(self):
        stats = snooker_inputs()
        stats.pop("player_potting_rating")
        stats.pop("potting_rating", None)
        self.assertEqual(self._sport(input_stats=stats)["model_status"], "inactive_missing_data")

    def test_malformed_text_inputs_do_not_activate(self):
        malformed = snooker_alias_inputs(potting_rating="bad", opp_potting_rating="bad", long_pot_success="text", century_proj="oops")
        analysis = self._screenshot(input_stats=malformed)["model_analysis"]
        self.assertNotEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["confirmed_bets"], [])

    def test_bad_odds_do_not_activate_from_default(self):
        self.assertEqual(self._sport(odds_american="bad odds")["model_status"], "inactive_missing_data")

    def test_odds_do_not_drive_final_probability(self):
        probs = [self._sport(odds_american=odds)["final_probability"] for odds in (-140, 100, 135)]
        self.assertLess(max(probs) - min(probs), 0.000001)

    def test_odds_change_only_market_outputs(self):
        low = self._sport(odds_american=-140)
        high = self._sport(odds_american=135)
        self.assertEqual(low["final_probability"], high["final_probability"])
        self.assertNotEqual(low["implied_probability"], high["implied_probability"])
        self.assertLess(low["edge_percent"], high["edge_percent"])

    def test_negative_edge_creates_no_bet(self):
        self.assertEqual(self._sport(odds_american=-2000)["status"], "evaluated_no_bet")

    def test_low_confidence_creates_no_bet(self):
        response = self._sport(odds_american=300, input_stats=snooker_inputs(book_count=1, fatigue_rating=0.85, injury_risk=0.42))
        self.assertEqual(response["status"], "evaluated_no_bet_low_confidence")

    def test_public_sharp_market_movement_are_enrichment_only(self):
        base = self._sport()["final_probability"]
        enriched = self._sport(input_stats=snooker_inputs(public_betting_percent=99, sharp_money_percent=1, market_movement=8))["final_probability"]
        self.assertEqual(base, enriched)

    def test_enrichment_alone_cannot_confirm(self):
        response = self._sport(input_stats={"public_betting_percent": 95, "sharp_money_percent": 90, "market_movement": 7})
        self.assertEqual(response["confirmed_bets"], [])
        self.assertEqual(response["suggested_stake"], 0)

    def test_match_winner_market_works(self):
        self.assert_active(self._sport(market="match_winner"))

    def test_moneyline_market_works(self):
        self.assert_active(self._sport(market="moneyline"))

    def test_frame_winner_market_works(self):
        self.assert_active(self._sport(market="frame_winner"))

    def test_rack_winner_market_works(self):
        self.assert_active(self._sport(market="rack_winner", input_stats=snooker_inputs(discipline="pool", match_format="race_to_9_racks", best_of_frames=0, race_to_frames=0, best_of_racks=17, race_to_racks=9, rack_number=1, frame_number=0)))

    def test_correct_score_market_works(self):
        self.assert_active(self._sport(market="correct_score", selection="10-8"))

    def test_frame_handicap_market_works(self):
        self.assert_active(self._sport(market="frame_handicap", input_stats=snooker_inputs(line=-2.5)))

    def test_rack_handicap_market_works(self):
        self.assert_active(self._sport(market="rack_handicap", input_stats=snooker_inputs(line=-1.5, discipline="pool", match_format="race_to_9_racks", best_of_frames=0, race_to_frames=0, best_of_racks=17, race_to_racks=9, rack_number=1, frame_number=0)))

    def test_total_frames_market_works(self):
        self.assert_active(self._sport(market="total_frames", selection="over", input_stats=snooker_inputs(line=16.5)))

    def test_total_racks_market_works(self):
        self.assert_active(self._sport(market="total_racks", selection="over", input_stats=snooker_inputs(line=8.5, discipline="pool", match_format="race_to_9_racks", best_of_frames=0, race_to_frames=0, best_of_racks=17, race_to_racks=9, rack_number=1, frame_number=0)))

    def test_highest_break_prop_works(self):
        self.assert_active(self._sport(market="highest_break", selection="Judd Trump"))

    def test_century_break_prop_works(self):
        self.assert_active(self._sport(market="century_break", selection="yes"))

    def test_player_total_centuries_prop_works(self):
        self.assert_active(self._sport(market="player_total_centuries", selection="Judd Trump over", input_stats=snooker_inputs(line=1.5, player_prop_line=1.5)))

    def test_player_total_50_breaks_prop_works(self):
        self.assert_active(self._sport(market="player_total_50_breaks", selection="Judd Trump over", input_stats=snooker_inputs(line=4.5, player_prop_line=4.5)))

    def test_first_frame_winner_market_works(self):
        self.assert_active(self._sport(market="first_frame_winner"))

    def test_final_frame_winner_market_works(self):
        self.assert_active(self._sport(market="final_frame_winner"))

    def test_race_to_frames_market_works(self):
        self.assert_active(self._sport(market="race_to_frames", selection="Judd Trump", input_stats=snooker_inputs(line=9.5)))

    def test_race_to_racks_market_works(self):
        self.assert_active(self._sport(market="race_to_racks", selection="Judd Trump", input_stats=snooker_inputs(line=8.5, discipline="pool", match_format="race_to_9_racks", best_of_frames=0, race_to_frames=0, best_of_racks=17, race_to_racks=9, rack_number=1, frame_number=0)))

    def test_alt_frame_handicap_market_works(self):
        self.assert_active(self._sport(market="alt_frame_handicap", input_stats=snooker_inputs(line=-3.5)))

    def test_alt_total_frames_market_works(self):
        self.assert_active(self._sport(market="alt_total_frames", selection="over", input_stats=snooker_inputs(line=17.5)))

    def test_alt_total_racks_market_works(self):
        self.assert_active(self._sport(market="alt_total_racks", selection="over", input_stats=snooker_inputs(line=9.5, discipline="pool", match_format="race_to_9_racks", best_of_frames=0, race_to_frames=0, best_of_racks=17, race_to_racks=9, rack_number=1, frame_number=0)))

    def test_calibration_outputs_exist(self):
        response = self._sport()
        self.assertEqual(response["discipline_calibration_applied"], "snooker")
        self.assertEqual(response["format_calibration_applied"], "frames")
        self.assertEqual(response["competition_calibration_applied"], "world_championship")
        self.assertTrue(response["potting_calibration_applied"])
        self.assertTrue(response["safety_calibration_applied"])
        self.assertTrue(response["break_building_calibration_applied"])
        self.assertTrue(response["pressure_calibration_applied"])

    def test_pool_billiards_and_unknown_calibrations(self):
        self.assertEqual(registry._snooker_discipline_calibration(snooker_inputs(discipline="nine ball", competition="Pool Tour", tournament="Mosconi Cup")), "pool")
        self.assertEqual(registry._snooker_discipline_calibration(snooker_inputs(discipline="billiards", competition="Billiards Open", tournament="Billiards Open")), "billiards")
        self.assertEqual(registry._snooker_format_calibration(snooker_inputs(discipline="pool", match_format="race_to_9_racks", best_of_frames=0, race_to_frames=0, best_of_racks=17, race_to_racks=9)), "racks")
        self.assertEqual(registry._snooker_format_calibration(snooker_inputs(match_format="custom_exhibition", best_of_frames=0, race_to_frames=0, best_of_racks=0, race_to_racks=0)), "unknown")
        self.assertEqual(registry._snooker_competition_calibration(snooker_inputs(competition="Invitational", tournament="Legends Exhibition", league=None, stage="Showcase")), "unknown")

    def test_potting_safety_break_building_and_pressure_edges_affect_probability(self):
        base = self._sport()["final_probability"]
        weaker = self._sport(input_stats=snooker_inputs(player_potting_rating=88, player_break_building_rating=89, player_safety_rating=86, player_pressure_rating=84, player_century_rate=0.24, player_50_break_rate=1.10))["final_probability"]
        self.assertLess(weaker, base)

    def test_no_confirmed_no_bet_same_selection_overlap(self):
        response = self._sport()
        confirmed = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["confirmed_bets"]}
        no_bets = {(bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection")) for bet in response["full_board_preview"]["no_bets"]}
        self.assertFalse(confirmed & no_bets)

    def test_full_board_output_includes_snooker_fields(self):
        response = self._sport()
        for field in ("confirmed_bets", "target_lines", "target_props", "target_alt_lines", "no_bets", "best_correlated_parlay", "value_ranking", "risk_ranking", "missing_inputs", "manual_review_required", "logbook_ready_rows"):
            self.assertIn(field, response)
        self.assertIn("snooker_input_contract", response)
        self.assertIsNotNone(response["snooker_projected_frames"])
        self.assertIsNotNone(response["snooker_projected_highest_break"])

    def test_logbook_fields_exist(self):
        row = self._sport()["logbook_ready_rows"][0]
        for field in ("confidence", "model_status", "decision", "stake", "suggested_stake", "league_calibration_applied", "discipline_calibration_applied", "format_calibration_applied", "competition_calibration_applied", "potting_calibration_applied", "safety_calibration_applied", "break_building_calibration_applied", "pressure_calibration_applied"):
            self.assertIn(field, row)

    def test_input_contract_contains_required_groups(self):
        contract = self._sport()["snooker_input_contract"]
        for group in ("required_core_inputs", "required_market_specific_inputs", "optional_enrichment_inputs", "player_prop_inputs"):
            self.assertIn(group, contract)

    def test_local_payload_contract_has_no_missing_inputs(self):
        ticket = registry.get_sport_model_config("snooker")["screenshot_alias_test_payload"]
        normalized = registry.normalize_sport_inputs_for_model(ticket["sport"], ticket["market"], ticket["selection"], ticket["input_stats"], ticket)
        self.assertEqual(normalized["missing_inputs_after_normalization"], [])

    def test_screenshot_alias_path_activates(self):
        analysis = self._screenshot()["model_analysis"]
        self.assertEqual(analysis["model_status"], "active")
        self.assertEqual(analysis["missing_inputs_after_normalization"], [])


if __name__ == "__main__":
    unittest.main()
