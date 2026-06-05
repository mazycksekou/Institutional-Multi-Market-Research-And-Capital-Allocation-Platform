import unittest

from automation_scheduler.ncaaw_free_data_loader import load_ncaaw_free_data_sample


class TestNcaawFreeDataLoader(unittest.TestCase):
    def test_ncaaw_loader_returns_safe_normalized_sample(self):
        result = load_ncaaw_free_data_sample("play_by_play", run_live_sample=False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["sport"], "basketball_ncaaw")
        self.assertGreater(result["records_tested"], 0)


if __name__ == "__main__":
    unittest.main()
