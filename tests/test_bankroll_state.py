import unittest
from pathlib import Path

from automation_scheduler.bankroll_state import default_bankroll_state, load_bankroll_state, save_bankroll_state


class BankrollStateTests(unittest.TestCase):
    def test_write_load_json(self):
        s = default_bankroll_state(2000)
        p = save_bankroll_state(s, Path("data/bankroll/test_bankroll.json"))
        loaded = load_bankroll_state(p)
        self.assertEqual(loaded["starting_bankroll"], 2000.0)

    def test_redacts_secrets(self):
        s = default_bankroll_state(1000)
        s["api_key"] = "secret_value"
        p = save_bankroll_state(s, Path("data/bankroll/test_bankroll_redact.json"))
        loaded = load_bankroll_state(p)
        self.assertEqual(loaded["api_key"], "[redacted]")


if __name__ == "__main__":
    unittest.main()
