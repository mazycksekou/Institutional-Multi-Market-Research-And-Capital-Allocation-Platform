import unittest

from src.analytics.institutional.liability_retirement_models import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalLiabilityRetirementModels(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 15)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)
            self.assertEqual(model["activation_status"], "research_only")

    def test_liability_model_scores_funding_and_alignment(self):
        result = run_model(
            "liability_driven_investing",
            {
                "asset_value": 90,
                "liability_value": 100,
                "duration_gap": 0.5,
                "contribution_rate": 0.08,
                "withdrawal_rate": 0.03,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertLess(result["funding_ratio"], 1.0)
        self.assertGreater(result["liability_match_score"], 80)

