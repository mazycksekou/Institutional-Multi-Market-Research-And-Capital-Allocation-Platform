import unittest

from math_models.institutional.factor_risk_models import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalFactorRiskModels(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 14)
        for model in models.values():
            self.assertEqual(model["activation_status"], "research_only")
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_risk_attribution_identifies_factor_concentration(self):
        result = run_model(
            "risk_attribution_model",
            {
                "factor_loadings": {"value": [1.5, 1.2], "momentum": [0.1, 0.0]},
                "factor_returns": {"value": 0.02, "momentum": 0.01},
                "portfolio_weights": {"A": 0.7, "B": 0.3},
                "benchmark_weights": {"A": 0.5, "B": 0.5},
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["concentration_risk"], 50)
        self.assertEqual(result["attribution_summary"]["largest_factor"], "value")

