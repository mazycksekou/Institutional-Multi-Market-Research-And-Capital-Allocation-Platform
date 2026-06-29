import json
import subprocess
import unittest
from copy import deepcopy

import src.market_intelligence.multi_sport_model_registry as registry


LIVE_SCRIPT_SPORTS = [
    "nba",
    "nfl",
    "mlb",
    "soccer",
    "rugby",
    "lacrosse",
    "table_tennis",
    "badminton",
    "pickleball",
    "darts",
    "snooker",
    "volleyball",
    "handball",
    "water_polo",
    "afl",
    "nhl",
    "tennis",
    "combat",
    "golf",
    "wnba",
    "ncaab",
    "ncaawb",
    "ncaaf",
    "f1",
    "formula_e",
    "nascar",
    "indycar",
    "motogp",
    "cricket",
    "cs2",
    "valorant",
    "lol",
    "dota2",
    "cod",
    "overwatch",
]


def same_selection_overlap(response):
    confirmed = {
        (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
        for bet in response.get("confirmed_bets", [])
    }
    no_bets = {
        (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
        for bet in response.get("no_bets", [])
    }
    board = response.get("full_board_preview") or {}
    no_bets |= {
        (bet.get("sport"), bet.get("event"), bet.get("market"), bet.get("selection"))
        for bet in board.get("no_bets", [])
    }
    return confirmed & no_bets


def analysis_payload_from_ticket(ticket):
    return {
        "sport": ticket.get("sport"),
        "league": ticket.get("league"),
        "event_id": ticket.get("event") or ticket.get("event_id"),
        "market": ticket.get("market"),
        "selection": ticket.get("selection"),
        "odds_american": ticket.get("odds_american"),
        "line": ticket.get("line") if ticket.get("line") is not None else ticket.get("total_line"),
        "bankroll": ticket.get("bankroll"),
        "unit_size": ticket.get("unit_size"),
        "risk_profile": ticket.get("risk_profile"),
        "input_stats": ticket.get("input_stats") or {},
    }


def load_script_payloads():
    script = (
        ". .\\scripts\\live_payloads.ps1; "
        "$payloads=[ordered]@{}; "
            "foreach($s in @('nba','nfl','mlb','soccer','rugby','lacrosse','table_tennis','badminton','pickleball','darts','snooker','volleyball','handball','water_polo','afl','nhl','tennis','combat','golf','wnba','ncaab','ncaawb','ncaaf','f1','formula_e','nascar','indycar','motogp','cricket','cs2','valorant','lol','dota2','cod','overwatch'))"
        "{ $payloads[$s]=New-LiveActivePayload -Sport $s }; "
        "$payloads | ConvertTo-Json -Depth 80 -Compress"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


class TestLiveSmokePayloadContract(unittest.TestCase):
    def assert_payload_complete_and_active(self, label, ticket):
        normalized = registry.normalize_sport_inputs_for_model(
            sport=ticket.get("sport"),
            market=ticket.get("market"),
            selection=ticket.get("selection"),
            input_stats=ticket.get("input_stats"),
            ticket=ticket,
        )
        self.assertEqual(normalized["missing_inputs_after_normalization"], [], label)
        response = registry.analyze_sport_model(analysis_payload_from_ticket(ticket))
        self.assertEqual(response["model_status"], "active", label)
        self.assertIsNotNone(response["final_probability"], label)
        self.assertNotEqual(response["decision"], "manual_review_required", label)
        self.assertFalse(same_selection_overlap(response), label)

    def test_registry_screenshot_alias_payloads_are_complete_for_active_sports(self):
        for sport in registry.get_sports_model_registry_response()["sports"]:
            if not sport.get("confirmed_bets_allowed"):
                continue
            payload = deepcopy(sport.get("screenshot_alias_test_payload") or {})
            with self.subTest(sport=sport["sport_key"]):
                self.assertTrue(sport.get("input_normalizer"))
                self.assertTrue(payload)
                self.assert_payload_complete_and_active(sport["sport_key"], payload)

    def test_power_shell_live_payload_builders_are_complete_for_active_smoke_sports(self):
        payloads = load_script_payloads()
        self.assertEqual(set(payloads), set(LIVE_SCRIPT_SPORTS))
        for sport_name, payload in payloads.items():
            with self.subTest(sport=sport_name):
                self.assert_payload_complete_and_active(sport_name, payload)

    def test_safety_payloads_stay_inactive_and_zero_stake_for_active_smoke_sports(self):
        payloads = load_script_payloads()
        for sport_name, payload in payloads.items():
            for bad_stats in ({}, "bad text input"):
                safety = deepcopy(payload)
                safety["input_stats"] = bad_stats
                with self.subTest(sport=sport_name, bad_type=type(bad_stats).__name__):
                    response = registry.analyze_sport_model(analysis_payload_from_ticket(safety))
                    self.assertEqual(response["confirmed_bets"], [])
                    self.assertEqual(response["suggested_stake"], 0)
                    self.assertNotEqual(response["model_status"], "active")


if __name__ == "__main__":
    unittest.main()
