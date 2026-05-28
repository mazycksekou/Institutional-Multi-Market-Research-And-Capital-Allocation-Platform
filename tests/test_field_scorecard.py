import unittest

from automation_scheduler.field_scorecard import build_field_scorecard


class TestFieldScorecard(unittest.TestCase):
    def test_scorecard_contains_all_fields_in_range(self):
        scorecard = build_field_scorecard(
            {
                "edge_percent": 12,
                "confidence": 0.8,
                "liquidity": 0.7,
                "movement_strength": 18,
                "expected_roi_percent": 11,
            }
        )
        self.assertEqual(len(scorecard), 13)
        for value in scorecard.values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 10)
