import unittest

from model_governance.champion_challenger import compare_champion_challenger


class TestChampionChallenger(unittest.TestCase):
    def test_can_keep_champion(self):
        result = compare_champion_challenger(
            champion_metrics={"calibration": 0.8, "clv": 0.03, "drawdown": 0.08, "roi_reality": 0.8, "stale_data_sensitivity": 0.1, "risk_adjusted_performance": 0.9},
            challenger_metrics={"calibration": 0.75, "clv": 0.02, "drawdown": 0.11, "roi_reality": 0.76, "stale_data_sensitivity": 0.2, "risk_adjusted_performance": 0.85, "sample_size": 200},
            promotion_gate_approved=True,
        )
        self.assertTrue(result["champion_kept"])

    def test_can_promote_challenger(self):
        result = compare_champion_challenger(
            champion_metrics={"calibration": 0.74, "clv": 0.01, "drawdown": 0.15, "roi_reality": 0.7, "stale_data_sensitivity": 0.3, "risk_adjusted_performance": 0.7},
            challenger_metrics={"calibration": 0.85, "clv": 0.04, "drawdown": 0.08, "roi_reality": 0.82, "stale_data_sensitivity": 0.1, "risk_adjusted_performance": 0.9, "sample_size": 200},
            promotion_gate_approved=True,
        )
        self.assertTrue(result["challenger_promoted"])

    def test_can_reject_or_request_more_data(self):
        rejected = compare_champion_challenger(
            champion_metrics={"calibration": 0.75, "clv": 0.02, "drawdown": 0.12, "roi_reality": 0.75, "stale_data_sensitivity": 0.25, "risk_adjusted_performance": 0.78},
            challenger_metrics={"calibration": 0.8, "clv": 0.03, "drawdown": 0.09, "roi_reality": 0.79, "stale_data_sensitivity": 0.15, "risk_adjusted_performance": 0.83, "sample_size": 200},
            promotion_gate_approved=False,
        )
        self.assertIn(rejected["decision"], {"challenger_rejected", "needs_more_data"})
        needs_more_data = compare_champion_challenger(
            champion_metrics={"calibration": 0.7, "clv": 0.01, "drawdown": 0.15, "roi_reality": 0.7, "stale_data_sensitivity": 0.2, "risk_adjusted_performance": 0.7},
            challenger_metrics={"calibration": 0.9, "clv": 0.04, "drawdown": 0.05, "roi_reality": 0.9, "stale_data_sensitivity": 0.1, "risk_adjusted_performance": 0.95, "sample_size": 20},
            promotion_gate_approved=True,
        )
        self.assertTrue(needs_more_data["needs_more_data"])
