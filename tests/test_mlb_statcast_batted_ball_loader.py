import unittest

from automation_scheduler.nfl_mlb_free_vs_paid_calibration import load_mlb_statcast_batted_ball_sample


class TestMlbStatcastBattedBallLoader(unittest.TestCase):
    def test_loader_returns_header_fields(self):
        csv_text = '"pitches","player_id","player_name","ba"\n"1","123","A Player",".250"\n'
        report = load_mlb_statcast_batted_ball_sample(fetch_fn=lambda url: csv_text)
        self.assertEqual(report["source_id"], "statcast_batted_ball_research_lane")
        self.assertEqual(report["records_validated"], 1)
        self.assertIn("player_id", report["fields_available"])


if __name__ == "__main__":
    unittest.main()
