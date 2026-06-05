import unittest

from automation_scheduler.nba_free_data_loader import load_nba_free_data_sample


class TestNbaFreeDataLoader(unittest.TestCase):
    def test_nba_loader_returns_safe_normalized_sample(self):
        result = load_nba_free_data_sample("schedule_results", run_live_sample=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["sport"], "basketball_nba")
        self.assertGreater(result["records_tested"], 0)
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])


if __name__ == "__main__":
    unittest.main()
