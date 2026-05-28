import unittest

from math_models.institutional.fixed_income_rates import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalFixedIncomeRates(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 13)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_fixed_income_model_outputs_duration_and_convexity(self):
        result = run_model(
            "duration_convexity_model",
            {
                "cash_flows": [3, 3, 103],
                "yield_curve": [0.03, 0.032, 0.035],
                "spread": 0.01,
                "price": 100,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["duration"], 0)
        self.assertGreater(result["convexity"], 0)

