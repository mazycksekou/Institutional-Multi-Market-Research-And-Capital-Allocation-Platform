import unittest
from model_governance.governance_audit_log import write_governance_audit_record

class TestGovernanceAuditLog(unittest.TestCase):
    def test_writes_json(self):
        r = write_governance_audit_record({'id':'test_audit_record','event_type':'test'})
        self.assertEqual(r['id'], 'test_audit_record')
