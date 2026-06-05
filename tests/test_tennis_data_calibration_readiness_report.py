import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisDataCalibrationReadinessReport(unittest.TestCase):
    def test_readiness_report_documents_blocked_policy_state(self):
        report = tennis_artifacts()["readiness_report"]
        model = report["models"][0]
        self.assertEqual(model["model"], "elo_serve_return_markov_tennis_model")
        self.assertEqual(model["recommendation"], "blocked_by_policy")
        self.assertIn("NO_BET suggested_stake=0 preserved", model["preserved_behavior"])


if __name__ == "__main__":
    unittest.main()
