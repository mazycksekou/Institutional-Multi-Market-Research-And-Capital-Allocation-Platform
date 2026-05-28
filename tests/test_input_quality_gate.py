import unittest

from model_governance.input_quality_gate import evaluate_input_quality


class TestInputQualityGate(unittest.TestCase):
    def test_input_gate_blocks_missing_malformed_and_stale(self):
        result = evaluate_input_quality(
            required_inputs=["odds_american", "market"],
            provided_inputs={"odds_american": "bad"},
            numeric_inputs=["odds_american"],
            input_age_seconds=1000,
        )
        self.assertTrue(result["blocked"])
        self.assertIn("market", result["missing_inputs"])
        self.assertIn("odds_american", result["malformed_inputs"])
        self.assertTrue(result["stale_inputs"])

