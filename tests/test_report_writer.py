import json
import unittest
from tempfile import TemporaryDirectory
from automation_scheduler.scheduler_config import get_default_scheduler_config
from automation_scheduler.report_writer import write_report


class TestReportWriter(unittest.TestCase):
    def test_writes_safe_report(self):
        with TemporaryDirectory() as tmp:
            c = get_default_scheduler_config(base_data_dir=tmp)
            r = write_report(c, report_name="r", payload={"secret": "x"})
            with open(r["path"], "r", encoding="utf-8") as f:
                p = json.load(f)
            self.assertEqual(p["payload"]["secret"], "[redacted]")
