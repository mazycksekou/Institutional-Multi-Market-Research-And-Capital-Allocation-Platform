import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.paper_decision_ledger import (
    create_paper_decision_record,
    load_paper_decision_state,
    load_paper_decisions,
    persist_paper_decisions_for_review_items,
)


class TestPaperDecisionLedger(unittest.TestCase):
    def test_create_record(self):
        with TemporaryDirectory() as tmp:
            record = create_paper_decision_record(
                {
                    "id": "review_1",
                    "provider_id": "kalshi_prediction_market",
                    "market_type": "prediction_market",
                    "ticker": "KXTEST",
                    "contract_id": "KXTEST",
                    "implied_probability": 0.55,
                    "recommendation_status": "review_only",
                    "execution_allowed": False,
                },
                base_data_dir=tmp,
            )
            self.assertFalse(record["execution_allowed"])
            self.assertTrue(record["paper_only"])
            self.assertEqual(record["outcome_status"], "pending")
            self.assertEqual(len(load_paper_decisions(tmp)), 1)

    def test_persist_run_ledger_preserves_scoring_and_survives_new_instance(self):
        with TemporaryDirectory() as tmp:
            meta = persist_paper_decisions_for_review_items(
                [
                    {
                        "id": "kalshi-review-1",
                        "provider_id": "kalshi_prediction_market",
                        "source_type": "prediction_market",
                        "market_type": "prediction_market",
                        "ticker": "KXTEST",
                        "contract_id": "KXTEST",
                        "yes_price": 0.55,
                        "price_source": "direct_price",
                        "implied_probability": 0.55,
                        "liquidity_tier": "low_liquidity",
                        "liquidity_score": 30,
                        "spread_score": 90,
                        "pricing_quality_score": 100,
                        "risk_score": 45,
                        "confidence_score": 61,
                        "review_priority_score": 68,
                        "reason_codes": ["prediction_market_review_only"],
                        "recommendation_status": "review_only",
                        "execution_allowed": True,
                        "provider_payload": {"raw": "drop"},
                        "api_key": "secret",
                    }
                ],
                run_id="run-test",
                snapshot_id="run-test",
                report_path="reports/scheduler_run_run-test.json",
                base_data_dir=tmp,
            )
            self.assertEqual(meta["paper_decisions_written"], 1)
            state = load_paper_decision_state(tmp)
            self.assertTrue(state["ledger_read_ok"])
            self.assertEqual(state["latest_run_id"], "run-test")
            self.assertEqual(state["items_read_count"], 1)
            record = state["items"][0]
            self.assertEqual(record["run_id"], "run-test")
            self.assertEqual(record["review_item_id"], "kalshi-review-1")
            self.assertEqual(record["liquidity_tier"], "low_liquidity")
            self.assertEqual(record["review_priority_score"], 68)
            self.assertFalse(record["execution_allowed"])
            self.assertTrue(record["paper_only"])
            rendered = str(record)
            self.assertNotIn("provider_payload", rendered)
            self.assertNotIn("secret", rendered)
