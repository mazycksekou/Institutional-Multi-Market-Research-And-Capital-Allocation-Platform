import unittest
from model_governance.data_lineage import create_lineage_record

class TestDataLineage(unittest.TestCase):
    def test_redact(self):
        r = create_lineage_record(api_key='x')
        self.assertEqual(r['api_key'], '[REDACTED]')
