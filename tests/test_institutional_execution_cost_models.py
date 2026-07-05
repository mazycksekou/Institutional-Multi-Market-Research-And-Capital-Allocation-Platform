import unittest

from src.analytics.institutional.execution_cost_models import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalExecutionCostModels(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 12)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_execution_cost_reduces_edge_when_costs_are_high(self):
        result = run_model(
            "implementation_shortfall_model",
            {
                "order_size": 50000,
                "average_daily_volume": 100000,
                "bid_ask_spread": 0.03,
                "volatility": 0.04,
                "raw_edge": 8.0,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertLess(result["cost_adjusted_edge"], 8.0)

