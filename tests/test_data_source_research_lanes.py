import unittest

from src.data.data_source_registry import build_registry_report


class TestDataSourceResearchLanes(unittest.TestCase):
    def setUp(self):
        self.report = build_registry_report()
        self.tasks = {task["lane_id"]: task for task in self.report["research_lanes"]["tasks"]}

    def test_every_incomplete_lane_has_research_task(self):
        for lane in self.report["lanes"]:
            if lane["lane_status"] in {"needs_external_research", "candidate_sources_available", "future_vendor_needed", "blocked_pending_source"}:
                self.assertIn(lane["lane_id"], self.tasks)

    def test_task_requirements_cover_access_terms_limits_mapping_and_outcomes(self):
        task = self.tasks["boxing"]
        requirements = " ".join(task["requirements"]).lower()
        self.assertIn("access", requirements)
        self.assertIn("license", requirements)
        self.assertIn("rate limits", requirements)
        self.assertIn("model inputs", requirements)
        self.assertIn("final outcome", requirements)
        self.assertIn("historical backfill", requirements)
        criteria = " ".join(task["acceptance_criteria"]).lower()
        self.assertIn("adapter feasibility", criteria)
        self.assertIn("sample response", criteria)

    def test_task_shape_and_priorities(self):
        for lane_id, task in self.tasks.items():
            self.assertEqual(task["research_task_id"], f"find_source_for_{lane_id}")
            self.assertEqual(task["status"], "open")
            self.assertIn(task["priority"], {"highest", "high", "medium", "low"})
            self.assertIn("required_model_inputs", task["required_data"])
            self.assertIn("outcome_fields_required", task["required_data"])
            self.assertIn("historical_backfill_fields_required", task["required_data"])

    def test_research_report_is_safe(self):
        research = self.report["research_lanes"]
        self.assertFalse(research["provider_write"])
        self.assertFalse(research["execution_allowed"])
        self.assertFalse(research["live_execution_enabled"])
        self.assertFalse(research["raw_payload_included"])


if __name__ == "__main__":
    unittest.main()
