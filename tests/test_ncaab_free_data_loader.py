import unittest

from automation_scheduler.ncaab_free_data_loader import load_ncaab_free_data_sample


class TestNcaabFreeDataLoader(unittest.TestCase):
    def test_ncaab_loader_returns_safe_normalized_sample(self):
        result = load_ncaab_free_data_sample("team_box_scores", run_live_sample=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["sport"], "basketball_ncaab")
        self.assertGreater(result["records_tested"], 0)


if __name__ == "__main__":
    unittest.main()
