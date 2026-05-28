import unittest

from automation_scheduler.clv_tracker import (
    calculate_clv_for_american_odds,
    calculate_positive_clv_rate,
    detect_clv_decay,
    summarize_clv_by_model,
)


class TestClvTracker(unittest.TestCase):
    def test_clv_for_american_odds(self):
        value = calculate_clv_for_american_odds(120, 100)
        self.assertGreater(value, 0)

    def test_positive_clv_rate(self):
        self.assertEqual(calculate_positive_clv_rate([1.0, -2.0, 0.5, 2.0]), 0.75)

    def test_detect_clv_decay(self):
        self.assertTrue(detect_clv_decay([3.2, 3.0, 2.8, -1.0, -1.2, -1.4]))

    def test_summarize_by_model(self):
        summary = summarize_clv_by_model(
            [
                {"model_id": "m1", "recommended_odds": 120, "closing_odds": 100},
                {"model_id": "m1", "recommended_odds": -105, "closing_odds": -115},
            ]
        )
        self.assertIn("m1", summary)
        self.assertIn("average_clv_percent", summary["m1"])


if __name__ == "__main__":
    unittest.main()

