import unittest

from src.analytics.institutional.derivatives_hedging import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalDerivativesHedging(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 14)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_derivatives_model_outputs_greeks(self):
        result = run_model(
            "black_scholes_merton",
            {
                "spot": 100,
                "strike": 100,
                "volatility": 0.2,
                "time_to_expiry": 0.5,
                "risk_free_rate": 0.03,
            },
        )
        self.assertEqual(result["status"], "ok")
        for greek in ("delta", "gamma", "vega", "theta", "rho"):
            self.assertIn(greek, result)

