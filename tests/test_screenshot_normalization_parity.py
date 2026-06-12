import asyncio
import unittest
from copy import deepcopy

import multi_sport_model_registry as registry
from tests.support.action_imports import ScreenshotAnalysisRequest, SportAnalysisRequest, action_analyze_sport_model, action_analyze_ticket_screenshot


def active_confirmed_sports():
    return [
        sport
        for sport in registry.get_sports_model_registry_response()["sports"]
        if sport.get("confirmed_bets_allowed")
    ]


def run_screenshot(payload):
    return asyncio.run(action_analyze_ticket_screenshot(ScreenshotAnalysisRequest(**payload)))


def run_direct(payload):
    return asyncio.run(action_analyze_sport_model(SportAnalysisRequest(**payload)))


def identity(row):
    return (
        str(row.get("sport") or row.get("sport_key") or "").lower(),
        str(row.get("event") or row.get("event_id") or "").lower(),
        str(row.get("market") or "").lower(),
        str(row.get("selection") or "").lower(),
    )


def assert_no_confirmed_no_bet_overlap(testcase, response):
    confirmed = set()
    no_bets = set()
    containers = [
        response,
        response.get("full_board_preview") or {},
        response.get("full_board") or {},
        response.get("model_analysis") or {},
        ((response.get("model_analysis") or {}).get("full_board_preview") or {}),
    ]
    for container in containers:
        for bet in container.get("confirmed_bets") or []:
            key = identity(bet)
            if key[2] and key[3]:
                confirmed.add(key)
        for bet in container.get("no_bets") or []:
            key = identity(bet)
            if key[2] and key[3]:
                no_bets.add(key)
    testcase.assertFalse(confirmed & no_bets)


class TestScreenshotNormalizationParity(unittest.TestCase):
    def test_every_active_confirmed_sport_has_live_style_screenshot_alias_payload(self):
        for sport in active_confirmed_sports():
            with self.subTest(sport=sport["sport_key"]):
                self.assertTrue(sport.get("input_normalizer"))
                payload = sport.get("screenshot_alias_test_payload")
                self.assertIsInstance(payload, dict)
                self.assertIsInstance(payload.get("input_stats"), dict)
                response = run_screenshot(deepcopy(payload))
                model = response.get("model_analysis") or {}
                self.assertTrue(response["ok"])
                self.assertTrue(model.get("model_name"))
                self.assertEqual(model.get("normalizer_used"), sport["input_normalizer"])
                self.assertNotEqual(model.get("model_status"), "inactive_missing_data")
                self.assertFalse(model.get("missing_inputs"))
                self.assertIsNotNone(model.get("final_probability"))
                self.assertIsNotNone(model.get("implied_probability"))
                self.assertNotEqual(model.get("status"), "manual_review_required")
                self.assertNotEqual(response.get("status"), "manual_review_required")
                self.assertTrue(response.get("logbook_ready_rows"))
                row = response["logbook_ready_rows"][0]
                for field in ("model_status", "confidence", "decision", "status", "stake", "suggested_stake"):
                    self.assertIn(field, row)
                assert_no_confirmed_no_bet_overlap(self, response)

    def test_direct_model_and_screenshot_alias_paths_reach_active_status(self):
        for sport in active_confirmed_sports():
            with self.subTest(sport=sport["sport_key"]):
                screenshot_payload = deepcopy(sport["screenshot_alias_test_payload"])
                normalization = registry.normalize_sport_inputs_for_model(
                    sport=screenshot_payload.get("sport"),
                    market=screenshot_payload.get("market"),
                    selection=screenshot_payload.get("selection"),
                    input_stats=screenshot_payload.get("input_stats"),
                    ticket=screenshot_payload,
                )
                direct_payload = {
                    "sport": sport["sport_key"],
                    "league": screenshot_payload.get("league"),
                    "event_id": screenshot_payload.get("event"),
                    "market": screenshot_payload.get("market"),
                    "selection": screenshot_payload.get("selection"),
                    "odds_american": screenshot_payload.get("odds_american"),
                    "line": screenshot_payload.get("line"),
                    "bankroll": screenshot_payload.get("bankroll"),
                    "unit_size": screenshot_payload.get("unit_size"),
                    "risk_profile": screenshot_payload.get("risk_profile"),
                    "input_stats": normalization["input_stats"],
                }
                direct = run_direct(direct_payload)
                screenshot = run_screenshot(screenshot_payload)
                model = screenshot.get("model_analysis") or {}
                self.assertEqual(direct.get("model_status"), "active")
                self.assertEqual(model.get("model_status"), "active")
                self.assertIsNotNone(direct.get("final_probability"))
                self.assertIsNotNone(model.get("final_probability"))
                self.assertNotEqual(direct.get("model_status"), "inactive_missing_data")
                self.assertNotEqual(model.get("model_status"), "inactive_missing_data")
                self.assertNotEqual(direct.get("status"), "manual_review_required")
                self.assertNotEqual(model.get("status"), "manual_review_required")

    def test_enrichment_only_payloads_cannot_create_confirmed_bets_for_active_sports(self):
        safety_inputs = [
            {"weather_wind_mph": 25, "weather_rating": 80},
            {"social_sentiment": 85, "crowd_consensus": 82, "public_betting_percent": 70},
            {"provider_status": "error", "current_odds": 100, "best_available_odds": 100},
            {"referee_name": "Official A", "official_sample_size": 200, "referee_profile": "fast stoppage"},
            {"course_name": "Augusta National", "course_difficulty": 9, "wind_rating": 4},
            {},
        ]
        for sport in active_confirmed_sports():
            base = deepcopy(sport["screenshot_alias_test_payload"])
            for stats in safety_inputs:
                with self.subTest(sport=sport["sport_key"], stats=sorted(stats.keys())):
                    payload = {
                        "sport": base.get("sport"),
                        "league": base.get("league"),
                        "event": base.get("event"),
                        "market": base.get("market"),
                        "selection": base.get("selection"),
                        "odds_american": base.get("odds_american"),
                        "bankroll": 1000,
                        "unit_size": 25,
                        "risk_profile": "moderate",
                        "input_stats": deepcopy(stats),
                    }
                    response = run_screenshot(payload)
                    model = response.get("model_analysis") or {}
                    self.assertTrue(response["ok"])
                    self.assertEqual(response["confirmed_bets"], [])
                    self.assertEqual(response.get("stake") or 0, 0)
                    self.assertEqual(response.get("suggested_stake") or 0, 0)
                    self.assertIn(model.get("model_status"), {"inactive_missing_data", "inactive"})
                    self.assertIn(response.get("decision"), {"NO_BET", None})
                    self.assertIn(model.get("status"), {"manual_review_required", "inactive_missing_data"})

    def test_golf_live_alias_regression_activates_before_missing_checks(self):
        payload = deepcopy(registry.get_sport_model_config("golf")["screenshot_alias_test_payload"])
        response = run_screenshot(payload)
        model = response["model_analysis"]
        self.assertTrue(response["ok"])
        self.assertEqual(model["model_status"], "active")
        self.assertIsNotNone(model["final_probability"])
        self.assertEqual(model["missing_inputs"], [])
        self.assertEqual(response["missing_inputs"], [])
        self.assertNotEqual(model["decision"], "manual_review_required")
        self.assertNotEqual(model["status"], "manual_review_required")
        if response["confirmed_bets"]:
            self.assertGreaterEqual(len(response["confirmed_bets"]), 1)
        confirmed_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["confirmed_bets"]
        }
        no_bet_keys = {
            (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
            for bet in response["no_bets"]
        }
        self.assertFalse(confirmed_keys & no_bet_keys)

    def test_provider_failure_with_full_stats_can_stay_active_but_provider_only_stays_inactive(self):
        full_payload = deepcopy(registry.get_sport_model_config("golf")["screenshot_alias_test_payload"])
        full_payload["input_stats"]["provider_status"] = "error"
        full = run_screenshot(full_payload)
        self.assertEqual(full["model_analysis"]["model_status"], "active")

        provider_only = deepcopy(full_payload)
        provider_only["input_stats"] = {"provider_status": "error", "current_odds": 100, "best_available_odds": 100}
        inactive = run_screenshot(provider_only)
        self.assertEqual(inactive["confirmed_bets"], [])
        self.assertEqual(inactive.get("stake") or 0, 0)
        self.assertIn(inactive["model_analysis"]["model_status"], {"inactive_missing_data", "inactive"})


if __name__ == "__main__":
    unittest.main()
