import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatSafeSourceSampler(unittest.TestCase):
    def test_safe_source_sampler_runs(self):
        report = combat_artifacts()["safe_sample_report"]
        self.assertTrue(report["ok"])
        self.assertGreater(report["sampled_source_count"], 0)
        self.assertGreater(report["metadata_only_records_added"], 0)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["raw_html_persisted"])
        decisions = {row["policy_decision"] for row in report["sample_rows"] if row["records_tested"] > 0}
        self.assertTrue(decisions.issubset({"accepted_for_automated_normalized_backfill", "accepted_for_metadata_only"}))


if __name__ == "__main__":
    unittest.main()
