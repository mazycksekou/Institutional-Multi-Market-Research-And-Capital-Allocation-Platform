import unittest
from model_governance.input_quality_gate import evaluate_input_quality

class TestInputQualityGate(unittest.TestCase):
    def test_blocks_missing(self):
        r = evaluate_input_quality(missing_inputs=1)
        self.assertTrue(r['blocked'])
