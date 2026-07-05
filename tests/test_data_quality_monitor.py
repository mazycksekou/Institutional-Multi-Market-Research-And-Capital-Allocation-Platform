import unittest
from src.analytics.model_governance.data_quality_monitor import evaluate_data_quality

class TestDataQualityMonitor(unittest.TestCase):
    def test_detects(self):
        r = evaluate_data_quality(duplicate_event=True)
        self.assertFalse(r['ok'])

    def test_kalshi_accepted_payload_is_usable(self):
        r = evaluate_data_quality(
            provider_id="kalshi_prediction_market",
            provider_type="prediction_market",
            validation_status="accepted",
            stale_provider_payload=False,
        )
        self.assertTrue(r["usable"])
        self.assertEqual(r["data_quality_result"], "approved")
