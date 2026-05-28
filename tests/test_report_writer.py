import json
import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.report_writer import write_report
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestReportWriter(unittest.TestCase):
    def test_report_writes_safe_json(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            result = write_report(config, report_name="daily", payload={"token": "secret", "value": 1})
            with open(result["path"], "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["payload"]["token"], "[redacted]")
            self.assertIn("ROI target is a filter target, not a guarantee.", payload["roi_target_disclaimer"])
