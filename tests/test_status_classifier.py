import unittest
from model_governance.status_classifier import classify_model_status

class TestStatusClassifier(unittest.TestCase):
    def test_verified_sport_model_active(self):
        r = classify_model_status(is_existing_verified_sport_model=True, tests_passed=True, input_contract_exists=True, deploy_verified=True, live_smoke_verified=True)
        self.assertEqual(r['activation_tier'], 'active_scoring_ready')
