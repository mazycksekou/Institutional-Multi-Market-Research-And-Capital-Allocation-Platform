import unittest

from automation_scheduler.wnba_free_data_loader import load_wnba_free_data_sample


class TestWnbaFreeDataLoader(unittest.TestCase):
    def test_wnba_loader_returns_safe_normalized_sample(self):
        result = load_wnba_free_data_sample("schedule_results", run_live_sample=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["sport"], "basketball_wnba")
        self.assertGreater(result["records_tested"], 0)
        self.assertFalse(result["raw_payload_included"])


if __name__ == "__main__":
    unittest.main()
