import unittest

from model_governance.model_card import build_card_from_inventory_item, create_model_card, validate_model_card
from model_governance.model_inventory import get_model_by_id


class TestModelCard(unittest.TestCase):
    def test_model_card_has_required_fields(self):
        card = build_card_from_inventory_item(get_model_by_id("sportsbook_side_total"))
        validation = validate_model_card(card)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["missing_fields"], [])

    def test_model_card_rejects_missing_fields(self):
        card = create_model_card(
            model_id="x",
            model_name="Sample",
            purpose="testing",
            market_type="sportsbook",
            time_horizon="same_day",
            research_basis="Documented",
            mathematical_summary="Summary",
            inputs=["a"],
            outputs=["b"],
            assumptions=["c"],
            limitations=["d"],
        )
        card["research_basis"] = ""
        validation = validate_model_card(card)
        self.assertFalse(validation["valid"])
        self.assertIn("research_basis", validation["missing_fields"])

