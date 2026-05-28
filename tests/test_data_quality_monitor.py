import unittest
from model_governance.data_quality_monitor import evaluate_data_quality

class TestDataQualityMonitor(unittest.TestCase):
    def test_detects(self):
        r = evaluate_data_quality(duplicate_event=True)
        self.assertFalse(r['ok'])
