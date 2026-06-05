import unittest

from automation_scheduler.nfl_mlb_free_vs_paid_calibration import build_mlb_draft_sample_verification_report


class TestMlbDraftSampleVerifier(unittest.TestCase):
    def test_report_parses_draft_payload(self):
        payload = {
            "drafts": [
                {
                    "rounds": [
                        {
                            "round": 1,
                            "picks": [
                                {"pickNumber": 1, "signed": True, "player": {"id": "p1"}, "team": {"id": "t1"}, "school": {"name": "School A"}},
                            ],
                        }
                    ]
                }
            ]
        }
        report = build_mlb_draft_sample_verification_report(fetch_fn=lambda url: payload)
        self.assertTrue(report["ok"])
        self.assertEqual(report["report_name"], "MLB_DRAFT_SAMPLE_VERIFICATION_REPORT")
        self.assertGreaterEqual(report["records_validated_total"], 1)
        self.assertIn("playerID", report["fields_verified_union"])


if __name__ == "__main__":
    unittest.main()
