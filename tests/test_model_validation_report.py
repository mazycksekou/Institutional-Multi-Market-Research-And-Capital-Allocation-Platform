import unittest
from src.analytics.reports import build_model_validation_report


class TestModelValidationReport(unittest.TestCase):
    def test_fields(self):
        r = build_model_validation_report("m", "research_only")
        self.assertIn("human_approval_required", r)
        self.assertIn("paper_tracking_summary", r)
        self.assertIn("clv_summary", r)
