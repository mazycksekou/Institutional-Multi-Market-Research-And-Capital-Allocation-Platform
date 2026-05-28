import unittest

from math_models.institutional.model_governance import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalModelGovernance(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 10)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_model_governance_detects_missing_validation(self):
        result = run_model(
            "independent_validation_status",
            {
                "validation_complete": False,
                "last_reviewed_days": 120,
                "drift_score": 0.65,
                "approval_committee": "",
                "audit_notes": ["missing challenger review"],
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["validation_required"])
        self.assertTrue(result["drift_detected"])
        self.assertEqual(result["approval_status"], "pending_review")

