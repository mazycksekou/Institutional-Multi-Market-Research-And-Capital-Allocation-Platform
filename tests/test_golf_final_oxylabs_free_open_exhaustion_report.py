import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfFinalOxylabsFreeOpenExhaustionReport(unittest.TestCase):
    def test_final_report_exists_and_is_safe(self):
        artifacts = golf_artifacts()
        report = artifacts["final_report"]
        self.assertEqual(report["new_overall_verdict"], "GOLF_FINAL_FREE_OPEN_EXHAUSTED")
        self.assertEqual(set(report["tours_included"]), {"PGA Tour", "DP World Tour", "LPGA", "Majors"})
        self.assertTrue(artifacts["manual_template_path"].exists())
        self.assertTrue(artifacts["manual_docs_path"].exists())
        self.assertTrue(artifacts["policy_docs_path"].exists())
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["paid_source_enabled_count"], 1)


if __name__ == "__main__":
    unittest.main()
