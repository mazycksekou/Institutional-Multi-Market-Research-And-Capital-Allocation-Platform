import unittest

from src.automation_scheduler_legacy.drawdown_controls import apply_drawdown_controls


class DrawdownControlsTests(unittest.TestCase):
    def test_drawdown_8_reduces(self):
        res = apply_drawdown_controls(0.04, {"current_drawdown_percent": 8})
        self.assertAlmostEqual(res["adjusted_stake_fraction"], 0.03, places=6)

    def test_drawdown_12_halves(self):
        res = apply_drawdown_controls(0.04, {"current_drawdown_percent": 12})
        self.assertAlmostEqual(res["adjusted_stake_fraction"], 0.02, places=6)

    def test_drawdown_20_pauses(self):
        res = apply_drawdown_controls(0.04, {"current_drawdown_percent": 20})
        self.assertEqual(res["adjusted_stake_fraction"], 0.0)
        self.assertEqual(res["action"], "pause_review")


if __name__ == "__main__":
    unittest.main()
