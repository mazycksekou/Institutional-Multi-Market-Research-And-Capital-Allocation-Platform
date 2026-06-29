import unittest

from src.analytics.institutional.performance_attribution import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalPerformanceAttribution(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 13)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_performance_attribution_outputs_transparent_metrics(self):
        result = run_model(
            "performance_attribution",
            {
                "period_returns": [0.02, 0.01, -0.005],
                "benchmark_returns": [0.015, 0.008, -0.003],
                "drawdowns": [-0.04, -0.02, -0.01],
                "capital_flows": [1000, -500, 0],
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("Past performance is not a guarantee of future results.", result["reporting_disclosures"])
        self.assertIn("average_return", result["performance_summary"])

