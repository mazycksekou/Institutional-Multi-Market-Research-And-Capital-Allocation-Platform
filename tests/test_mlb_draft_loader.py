import unittest

from automation_scheduler.nfl_mlb_free_vs_paid_calibration import load_mlb_draft_sample


class TestMlbDraftLoader(unittest.TestCase):
    def test_loader_reports_working_draft_endpoint_shape(self):
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
        report = load_mlb_draft_sample(fetch_fn=lambda url: payload)
        self.assertEqual(report["source_id"], "draft_lahman")
        self.assertGreaterEqual(report["records_validated"], 1)


if __name__ == "__main__":
    unittest.main()
