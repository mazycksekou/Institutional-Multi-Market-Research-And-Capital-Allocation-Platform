import unittest

from math_models.institutional.macro_regime_models import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalMacroRegimeModels(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 12)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_macro_regime_can_reduce_model_trust(self):
        result = run_model(
            "macro_regime_classifier",
            {
                "growth_score": 0.2,
                "inflation_score": 0.8,
                "liquidity_score": 0.3,
                "volatility_score": 0.9,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertLess(result["model_trust_adjustment"], 1.0)
        self.assertGreater(result["recession_probability"], 0.4)

