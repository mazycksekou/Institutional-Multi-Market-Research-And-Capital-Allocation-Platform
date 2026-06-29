from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import src.services.bet_log as bet_log
from tests.support.action_imports import ActionBetLogRequest


def _entry(**extra):
    payload = {
        "sport_key": "baseball_mlb",
        "event_id": "event-1",
        "event": "Team A at Team B",
        "sportsbook": "draftkings",
        "market": "h2h",
        "selection": "Team A",
        "odds_american": -110,
        "actual_odds_taken": -110,
        "stake": 25,
        "unit_size": 25,
        "bankroll_at_bet": 1000,
        "probability_type": "blended_market_and_projection",
        "suggested_stake": 25,
        "decision": "bet",
        "user_action": "bet_placed",
    }
    payload.update(extra)
    return bet_log.create_bet_log_entry(payload)


def _request_entry(**extra):
    payload = ActionBetLogRequest(**extra)
    return bet_log.create_bet_log_entry(payload.model_dump(exclude_none=True))


class TestBetLog(unittest.TestCase):
    def test_log_bet_creates_a_bet_id(self):
        entry = _entry()

        self.assertTrue(entry["bet_id"])

    def test_log_bet_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bet_log.jsonl"
            entry = _entry()

            bet_log.append_bet_log_entry(entry, path)

            self.assertTrue(path.exists())
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["bet_id"], entry["bet_id"])

    def test_log_bet_accepts_numeric_confidence(self):
        entry = _request_entry(confidence=40)

        self.assertEqual(entry["confidence"], 40.0)

    def test_log_bet_accepts_float_confidence(self):
        entry = _request_entry(confidence=40.0)

        self.assertEqual(entry["confidence"], 40.0)

    def test_log_bet_accepts_string_confidence(self):
        entry = _request_entry(confidence="40")

        self.assertEqual(entry["confidence"], 40.0)

    def test_log_bet_accepts_missing_confidence(self):
        entry = _request_entry()

        self.assertIsNone(entry["confidence"])

    def test_log_bet_accepts_null_confidence(self):
        entry = _request_entry(confidence=None)

        self.assertIsNone(entry["confidence"])

    def test_no_bet_user_placement_marks_ignored_no_bet(self):
        entry = _entry(decision="no_bet", user_action="bet_placed")

        self.assertEqual(entry["error_type"], "ignored_no_bet")

    def test_bad_odds_marks_bad_price(self):
        entry = _entry(actual_odds_taken=-130, minimum_playable_odds=-120)

        self.assertEqual(entry["error_type"], "bad_price")

    def test_over_stake_marks_overstaked(self):
        entry = _entry(stake=50, suggested_stake=25)

        self.assertEqual(entry["error_type"], "overstaked")

    def test_market_derived_bet_placement_marks_market_only_bet(self):
        entry = _entry(probability_type="market_derived", user_action="bet_placed")

        self.assertEqual(entry["error_type"], "market_only_bet")

    def test_manual_override_avoids_market_only_bet(self):
        entry = _entry(
            probability_type="market_derived",
            user_action="bet_placed",
            manual_override=True,
        )

        self.assertIsNone(entry["error_type"])

    def test_log_result_calculates_win_profit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bet_log.jsonl"
            entry = _entry(actual_odds_taken=150, stake=20)
            bet_log.append_bet_log_entry(entry, path)

            updated = bet_log.update_bet_result(entry["bet_id"], "win", path=path)

            self.assertEqual(updated["profit_loss"], 30)

    def test_log_result_calculates_loss_profit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bet_log.jsonl"
            entry = _entry(stake=20)
            bet_log.append_bet_log_entry(entry, path)

            updated = bet_log.update_bet_result(entry["bet_id"], "loss", path=path)

            self.assertEqual(updated["profit_loss"], -20)

    def test_log_result_handles_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bet_log.jsonl"
            entry = _entry(stake=20)
            bet_log.append_bet_log_entry(entry, path)

            updated = bet_log.update_bet_result(entry["bet_id"], "push", path=path)

            self.assertEqual(updated["profit_loss"], 0)

    def test_performance_summary_calculates_roi_and_yield(self):
        entries = [
            _entry(result="win", profit_loss=20, stake=100),
            _entry(result="loss", profit_loss=-10, stake=100),
        ]

        summary = bet_log.get_performance_summary(entries)

        self.assertEqual(summary["total_bets"], 2)
        self.assertEqual(summary["wins"], 1)
        self.assertEqual(summary["losses"], 1)
        self.assertEqual(summary["total_staked"], 200)
        self.assertEqual(summary["profit_loss"], 10)
        self.assertEqual(summary["roi"], 5)
        self.assertEqual(summary["yield"], 5)

    def test_bankroll_summary_returns_bankroll_movement(self):
        entries = [
            _entry(bankroll_at_bet=1000, profit_loss=30),
            _entry(bankroll_at_bet=1030, profit_loss=-10),
        ]

        summary = bet_log.get_bankroll_summary(entries)

        self.assertEqual(summary["starting_bankroll"], 1000)
        self.assertEqual(summary["profit_loss"], 20)
        self.assertEqual(summary["current_bankroll"], 1020)
        self.assertEqual(summary["bankroll_movement"], 20)

    def test_clv_report_calculates_clv_when_closing_odds_exist(self):
        entries = [_entry(actual_odds_taken=120, closing_odds=100)]

        report = bet_log.get_clv_report(entries)

        self.assertEqual(report["count"], 1)
        self.assertGreater(report["bets"][0]["clv_percent"], 0)
        self.assertEqual(report["positive_clv_count"], 1)

    def test_empty_log_returns_clean_summary(self):
        summary = bet_log.get_performance_summary([])

        self.assertEqual(summary["total_bets"], 0)
        self.assertEqual(summary["total_staked"], 0)
        self.assertEqual(summary["profit_loss"], 0)
        self.assertEqual(summary["roi"], 0)
        self.assertEqual(summary["yield"], 0)
        self.assertEqual(summary["error_counts"], {})

    def test_data_file_is_not_required_to_exist_before_first_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "bet_log.jsonl"

            self.assertFalse(path.exists())
            bet_log.append_bet_log_entry(_entry(), path)

            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
