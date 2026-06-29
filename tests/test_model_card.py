import unittest
from src.analytics.model_governance.model_card import create_model_card, validate_model_card

class TestModelCard(unittest.TestCase):
    def test_model_card_requires_mandatory_fields(self):
        card = create_model_card(model_id='m1', model_name='M1')
        self.assertFalse(validate_model_card(card)['valid'])
