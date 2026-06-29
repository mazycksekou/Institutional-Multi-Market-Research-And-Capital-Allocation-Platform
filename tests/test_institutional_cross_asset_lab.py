import json
import tempfile
import unittest
from pathlib import Path

from src.services.streamlit_dashboard_facade import get_institutional_lab_health, run_institutional_lab
from src.services.streamlit_dashboard_facade import get_default_scheduler_config
from src.automation_scheduler_legacy.stake_sizing_simulator import simulate_stake_plan


class TestInstitutionalCrossAssetLab(unittest.TestCase):
    def _seed_prediction_market_data(self, root: Path):
        (root / "review_queue").mkdir(parents=True, exist_ok=True)
        (root / "outcomes").mkdir(parents=True, exist_ok=True)
        (root / "paper_ledger").mkdir(parents=True, exist_ok=True)
        review = {
            "items": [
                {
                    "id": "review-1",
                    "provider_id": "kalshi_prediction_market",
                    "provider": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "contract_id": "KXTEST",
                    "ticker": "KXTEST",
                    "yes_bid": 0.49,
                    "yes_ask": 0.51,
                    "yes_price": 0.5,
                    "implied_probability": 0.5,
                    "volume": 1000,
                    "open_interest": 1200,
                    "liquidity_score": 80,
                    "pricing_quality_score": 95,
                    "created_at": "2026-05-30T12:00:00+00:00",
                    "execution_allowed": False,
                }
            ]
        }
        outcomes = {
            "items": [
                {
                    "provider": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "contract_id": "KXTEST",
                    "outcome_status": "settled",
                    "final_outcome": "yes",
                    "settled_at": "2026-05-30T13:00:00+00:00",
                }
            ]
        }
        (root / "review_queue" / "latest.json").write_text(json.dumps(review), encoding="utf-8")
        (root / "outcomes" / "latest.json").write_text(json.dumps(outcomes), encoding="utf-8")

    def test_lab_runs_as_isolated_sidecar_and_writes_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_prediction_market_data(root)
            before_review = (root / "review_queue" / "latest.json").read_text(encoding="utf-8")
            before_outcomes = (root / "outcomes" / "latest.json").read_text(encoding="utf-8")
            result = run_institutional_lab(
                base_data_dir=tmp,
                asset_classes=["prediction_market", "stock", "sportsbook"],
                persist_lab_report=True,
                persist_outcomes=False,
                deepseek_review=False,
                execution_simulation=False,
            )
            after_review = (root / "review_queue" / "latest.json").read_text(encoding="utf-8")
            after_outcomes = (root / "outcomes" / "latest.json").read_text(encoding="utf-8")
            self.assertTrue((root / "institutional_lab" / "latest.json").exists())
            self.assertTrue((root / result["daily_report_path"]).exists())
        self.assertEqual(before_review, after_review)
        self.assertEqual(before_outcomes, after_outcomes)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source_counts"]["prediction_market"], 1)
        self.assertEqual(result["matched_outcomes_count"], 1)
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["live_execution_enabled"])

    def test_lab_can_run_without_stock_or_sportsbook_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_prediction_market_data(root)
            result = run_institutional_lab(base_data_dir=tmp, asset_classes=["prediction_market", "stock", "sportsbook"])
        self.assertEqual(result["source_counts"]["prediction_market"], 1)
        self.assertEqual(result["source_counts"]["stock"], 0)
        self.assertEqual(result["source_counts"]["sportsbook"], 0)
        self.assertIn("stock", result["unavailable"])

    def test_health_is_safe_before_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            health = get_institutional_lab_health(base_data_dir=tmp)
        self.assertTrue(health["ok"])
        self.assertFalse(health["provider_write"])
        self.assertFalse(health["execution_allowed"])
        self.assertFalse(health["live_execution_enabled"])

    def test_lab_does_not_change_stake_sizing_behavior(self):
        candidate = {
            "candidate_type": "arbitrage_candidate",
            "estimated_roi_percent": 2.5,
            "stake_plan": [{"selection": "A", "stake": 50}, {"selection": "B", "stake": 50}],
            "max_gain": 2.5,
            "max_loss": 97.5,
        }
        before = simulate_stake_plan(candidate, bankroll=1000, risk_profile="low", max_loss_cap=8)
        with tempfile.TemporaryDirectory() as tmp:
            run_institutional_lab(base_data_dir=tmp, asset_classes=["prediction_market"])
        after = simulate_stake_plan(candidate, bankroll=1000, risk_profile="low", max_loss_cap=8)
        self.assertEqual(before, after)

    def test_lab_does_not_change_existing_score_thresholds(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = dict(get_default_scheduler_config(base_data_dir=tmp)["score_thresholds"])
            run_institutional_lab(base_data_dir=tmp, asset_classes=["prediction_market"])
            after = dict(get_default_scheduler_config(base_data_dir=tmp)["score_thresholds"])
        self.assertEqual(before, after)

    def test_rejects_non_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run_institutional_lab(base_data_dir=tmp, dry_run=False)


if __name__ == "__main__":
    unittest.main()
