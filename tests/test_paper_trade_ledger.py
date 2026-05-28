import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.paper_trade_ledger import (
    create_paper_entry,
    load_paper_ledger,
    settle_paper_entry,
    summarize_paper_ledger,
    update_closing_line,
)


class TestPaperTradeLedger(unittest.TestCase):
    def test_create_entry_is_paper_only(self):
        with TemporaryDirectory() as tmp:
            entry = create_paper_entry(
                {
                    "recommendation_id": "rec1",
                    "model_id": "m1",
                    "model_group": "sports",
                    "market_type": "moneyline",
                    "recommended_odds": -110,
                    "paper_stake": 10,
                },
                base_dir=tmp,
            )
            self.assertTrue(entry["human_approval_required"])
            self.assertFalse(entry["auto_execution_enabled"])
            self.assertEqual(entry["recommended_action"], "paper_tracking")

    def test_update_closing_line(self):
        with TemporaryDirectory() as tmp:
            create_paper_entry(
                {
                    "recommendation_id": "rec2",
                    "model_id": "m1",
                    "model_group": "sports",
                    "market_type": "moneyline",
                    "recommended_odds": 120,
                    "paper_stake": 10,
                },
                base_dir=tmp,
            )
            updated = update_closing_line("rec2", 100, base_dir=tmp)
            self.assertEqual(updated["closing_odds"], 100.0)

    def test_settle_win_loss_push(self):
        with TemporaryDirectory() as tmp:
            for status, rec_id in [("win", "recw"), ("loss", "recl"), ("push", "recp")]:
                create_paper_entry(
                    {
                        "recommendation_id": rec_id,
                        "model_id": "m1",
                        "model_group": "sports",
                        "market_type": "moneyline",
                        "recommended_odds": 100,
                        "paper_stake": 10,
                    },
                    base_dir=tmp,
                )
                settled = settle_paper_entry(rec_id, status, base_dir=tmp)
                self.assertEqual(settled["settlement_status"], "settled")
            summary = summarize_paper_ledger(base_dir=tmp)
            self.assertEqual(summary["win_count"], 1)
            self.assertEqual(summary["loss_count"], 1)
            self.assertEqual(summary["push_count"], 1)

    def test_no_real_execution_side_effects(self):
        with TemporaryDirectory() as tmp:
            create_paper_entry(
                {
                    "recommendation_id": "rec3",
                    "model_id": "m1",
                    "model_group": "sports",
                    "market_type": "spread",
                    "recommended_odds": -110,
                    "paper_stake": 10,
                },
                base_dir=tmp,
            )
            ledger = load_paper_ledger(base_dir=tmp)
            self.assertEqual(len(ledger), 1)
            self.assertFalse(ledger[0]["auto_execution_enabled"])


if __name__ == "__main__":
    unittest.main()

