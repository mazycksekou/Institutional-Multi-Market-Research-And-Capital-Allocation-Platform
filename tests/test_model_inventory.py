import unittest

from model_governance import contains_banned_language
from model_governance.model_inventory import get_model_inventory, inventory_counts


class TestModelInventory(unittest.TestCase):
    def test_inventory_registers_major_model_families(self):
        inventory = get_model_inventory()
        families = {item["model_family"] for item in inventory}
        self.assertTrue(
            {
                "sportsbook_models",
                "stock_models",
                "prediction_market_models",
                "institutional_investment_models",
                "cross_book_models",
                "kelly_models",
                "automation_models",
            }.issubset(families)
        )
        required_fields = {
            "model_id",
            "model_name",
            "model_family",
            "model_purpose",
            "market_type",
            "time_horizon",
            "activation_tier",
            "owner",
            "inputs_required",
            "outputs_produced",
            "assumptions",
            "limitations",
            "evidence_score",
            "input_quality_score",
            "calibration_score",
            "backtest_score",
            "walk_forward_score",
            "drift_score",
            "risk_score",
            "governance_score",
            "can_affect_review_queue",
            "can_affect_stake_sizing",
            "can_affect_alerts",
            "can_affect_final_decision",
            "human_approval_required",
        }
        for item in inventory:
            self.assertEqual(required_fields.difference(item), set())
            self.assertTrue(item["human_approval_required"])
        self.assertFalse(contains_banned_language(inventory))

    def test_inventory_counts_cover_activation_tiers(self):
        counts = inventory_counts()
        self.assertGreater(counts["model_inventory_count"], 0)
        self.assertGreaterEqual(counts["research_only_count"], 1)
        self.assertGreaterEqual(counts["production_candidate_count"], 1)
