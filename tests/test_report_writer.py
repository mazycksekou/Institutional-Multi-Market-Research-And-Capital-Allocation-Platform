import json
import unittest
from tempfile import TemporaryDirectory
from src.services.streamlit_dashboard_facade import get_default_scheduler_config
from src.services.streamlit_dashboard_facade import write_report


class TestReportWriter(unittest.TestCase):
    def test_writes_safe_report(self):
        with TemporaryDirectory() as tmp:
            c = get_default_scheduler_config(base_data_dir=tmp)
            r = write_report(c, report_name="r", payload={"secret": "x"})
            with open(r["path"], "r", encoding="utf-8") as f:
                p = json.load(f)
            self.assertEqual(p["payload"]["secret"], "[redacted]")
