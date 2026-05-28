import unittest

from math_models.institutional.tax_aware_models import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalTaxAwareModels(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 7)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_tax_aware_model_flags_wash_sale_risk(self):
        result = run_model(
            "wash_sale_risk_checker",
            {
                "pre_tax_return": 0.08,
                "tax_rate": 0.3,
                "unrealized_loss": -0.05,
                "recent_sale_days": 10,
                "account_type": "taxable_account",
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["wash_sale_risk"], 1.0)

