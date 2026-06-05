import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisFinalOxylabsFreeOpenExhaustionReport(unittest.TestCase):
    def test_final_report_is_safe_and_complete(self):
        report = tennis_artifacts()["final_report"]
        self.assertEqual(report["new_overall_verdict"], "TENNIS_FINAL_NO_NEW_DATA_BUT_EXHAUSTED")
        self.assertEqual(report["raw_html_persisted"], False)
        self.assertEqual(report["raw_payload_included"], False)
        self.assertEqual(report["secrets_included"], False)
        self.assertEqual(report["provider_write"], False)
        self.assertEqual(report["execution_allowed"], False)
        self.assertEqual(report["paid_source_enabled_count"], 1)


if __name__ == "__main__":
    unittest.main()
