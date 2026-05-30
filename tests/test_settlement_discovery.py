import unittest

from automation_scheduler.settlement_discovery import classify_kalshi_settlement, discover_kalshi_settlements_for_pending_rows


class TestSettlementDiscoveryExplicitOnly(unittest.TestCase):
    def test_explicit_yes_and_no_create_candidates(self):
        pending = [
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXYES"},
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXNO"},
        ]
        report = discover_kalshi_settlements_for_pending_rows(
            pending,
            read_only_records=[
                {"contract_id": "KXYES", "result": "yes", "status": "finalized", "settlement_time": "2026-05-30T00:00:00Z"},
                {"contract_id": "KXNO", "result": "no", "status": "finalized", "settlement_time": "2026-05-30T00:00:00Z"},
            ],
        )
        self.assertEqual(report["completion_candidates_count"], 2)
        self.assertEqual(report["settled_yes_count"], 1)
        self.assertEqual(report["settled_no_count"], 1)

    def test_not_settled_unknown_and_closed_without_result_do_not_persist(self):
        pending = [
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXACTIVE"},
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXUNKNOWN"},
            {"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXCLOSED"},
        ]
        report = discover_kalshi_settlements_for_pending_rows(
            pending,
            read_only_records=[
                {"contract_id": "KXACTIVE", "status": "active", "yes_price": 1.0},
                {"contract_id": "KXUNKNOWN"},
                {"contract_id": "KXCLOSED", "status": "closed", "yes_price": 1.0},
            ],
        )
        self.assertEqual(report["completion_candidates_count"], 0)
        self.assertEqual(report["not_settled_count"], 1)
        self.assertEqual(report["unknown_count"], 2)

    def test_current_price_never_creates_outcome(self):
        classification = classify_kalshi_settlement({"contract_id": "KXPRICE", "status": "closed", "last_price": 1.0, "yes_price": 1.0})
        self.assertEqual(classification["classification"], "unknown")
        self.assertNotEqual(classification.get("evidence_type"), "explicit_settlement_field")

    def test_void_cancelled_explicit_field_creates_candidate(self):
        report = discover_kalshi_settlements_for_pending_rows(
            [{"provider": "kalshi_prediction_market", "market_type": "prediction_market", "contract_id": "KXVOID"}],
            read_only_records=[{"contract_id": "KXVOID", "result": "void", "status": "cancelled", "settlement_time": "2026-05-30T00:00:00Z"}],
        )
        self.assertEqual(report["void_cancelled_count"], 1)
        self.assertEqual(report["completion_candidates_count"], 1)
        self.assertEqual(report["completion_candidates"][0]["final_outcome"], "void")


if __name__ == "__main__":
    unittest.main()
