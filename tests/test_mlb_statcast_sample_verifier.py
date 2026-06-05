import unittest

from automation_scheduler.nfl_mlb_free_vs_paid_calibration import build_mlb_statcast_sample_verification_report


class TestMlbStatcastSampleVerifier(unittest.TestCase):
    def test_report_parses_official_csv_sample(self):
        csv_text = '"pitches","player_id","player_name","ba"\n"1","123","A Player",".250"\n"2","456","B Player",".300"\n'
        report = build_mlb_statcast_sample_verification_report(fetch_fn=lambda url: csv_text)
        self.assertTrue(report["ok"])
        self.assertEqual(report["report_name"], "MLB_STATCAST_SAMPLE_VERIFICATION_REPORT")
        self.assertGreater(report["sample_verified_count"], 0)
        self.assertIn("pitches", report["fields_verified_union"])


if __name__ == "__main__":
    unittest.main()
