import unittest
from src.analytics.model_governance.data_lineage import create_lineage_record

class TestDataLineage(unittest.TestCase):
    def test_redact(self):
        r = create_lineage_record(api_key='x')
        self.assertEqual(r['api_key'], '[REDACTED]')
        self.assertIn('redaction_status', r)

    def test_kalshi_provider_defaults_prediction_market(self):
        r = create_lineage_record(provider_id="kalshi_prediction_market")
        self.assertEqual(r["provider_type"], "prediction_market")
        self.assertEqual(r["source_type"], "prediction_market")
        self.assertIn("settlement_rule_status", r)
