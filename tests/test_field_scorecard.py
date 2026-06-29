import unittest

from src.automation_scheduler_legacy.field_scorecard import build_field_scorecard


class TestFieldScorecard(unittest.TestCase):
    def test_scorecard_contains_all_fields_in_range(self):
        scorecard = build_field_scorecard(
            {
                "edge_percent": 12,
                "ev_percent": 6,
                "confidence": 0.8,
                "liquidity": 0.7,
                "movement_strength": 18,
                "line_match_confidence": 92,
                "expected_roi_percent": 11,
            }
        )
        self.assertEqual(len(scorecard), 23)
        for value in scorecard.values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 10)
