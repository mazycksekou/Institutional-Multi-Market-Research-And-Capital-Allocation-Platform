import unittest

from pathlib import Path

from tests.combat_test_support import combat_artifacts


class TestCombatFinalOxylabsFreeOpenExhaustionReport(unittest.TestCase):
    def test_final_report_exists(self):
        artifacts = combat_artifacts()
        report = artifacts["final_report"]
        self.assertIn(report["new_overall_verdict"], {"COMBAT_FINAL_FREE_OPEN_EXHAUSTED", "COMBAT_FINAL_NO_NEW_DATA_BUT_EXHAUSTED"})
        self.assertEqual(set(report["combat_types_included"]), {"UFC", "MMA", "Boxing"})
        self.assertTrue(Path(artifacts["manual_template_path"]).exists())
        self.assertTrue(Path(artifacts["manual_docs_path"]).exists())
        self.assertTrue(Path(artifacts["policy_docs_path"]).exists())
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["secrets_included"])
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])
        self.assertEqual(report["paid_source_enabled_count"], 1)


if __name__ == "__main__":
    unittest.main()
