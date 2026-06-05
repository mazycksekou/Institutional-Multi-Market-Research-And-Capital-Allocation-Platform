import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfCandidateSourcePolicyInventory(unittest.TestCase):
    def test_candidate_inventory_is_exhaustive_for_scope(self):
        report = golf_artifacts()["candidate_inventory"]
        names = {row["source_name"] for row in report["candidate_source_rows"]}
        self.assertEqual(report["candidate_source_count"], 15)
        self.assertIn("PGA Tour official pages", names)
        self.assertIn("DP World Tour official pages", names)
        self.assertIn("LPGA official pages", names)
        self.assertIn("Major championship official pages", names)


if __name__ == "__main__":
    unittest.main()
