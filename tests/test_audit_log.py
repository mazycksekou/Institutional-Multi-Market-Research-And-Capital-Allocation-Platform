import unittest
from tempfile import TemporaryDirectory

from src.services.streamlit_dashboard_facade import append_audit_record, read_audit_records
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestAuditLog(unittest.TestCase):
    def test_audit_log_writes_safe_records(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            append_audit_record(config, {"event": "run", "api_key": "secret"})
            records = read_audit_records(config)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["record"]["api_key"], "[redacted]")
