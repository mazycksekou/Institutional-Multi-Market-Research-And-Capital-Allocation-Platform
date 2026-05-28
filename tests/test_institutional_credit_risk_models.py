import unittest

from math_models.institutional.credit_risk_models import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalCreditRiskModels(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 12)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_credit_model_outputs_expected_loss(self):
        result = run_model(
            "expected_default_frequency",
            {
                "leverage_ratio": 4,
                "interest_coverage": 2,
                "spread": 0.04,
                "recovery_rate": 0.4,
                "exposure": 1000000,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["expected_loss"], 0)
        self.assertGreater(result["probability_of_default"], 0)

