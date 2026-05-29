import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.paper_decision_ledger import create_paper_decision_record, load_paper_decisions


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
            self.assertEqual(len(load_paper_decisions(tmp)), 1)
