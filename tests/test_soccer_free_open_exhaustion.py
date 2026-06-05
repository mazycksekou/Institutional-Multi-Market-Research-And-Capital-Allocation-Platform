import unittest
from contextlib import ExitStack
from unittest.mock import patch

from automation_scheduler.soccer_free_open_exhaustion import build_soccer_manual_import_templates, build_and_write_all_soccer_free_open_exhaustion_reports


class TestSoccerFreeOpenExhaustion(unittest.TestCase):
    def test_manual_templates_include_unresolved_rows(self):
        report = build_soccer_manual_import_templates(
            source_ledger={"source_ledger_rows": [{"sport": "soccer", "lane_name": "injuries_availability", "field_or_feature_group": "injuries", "free_or_paid_category": "free_open_manual_import_needed", "final_reason": "manual", "candidate_source_name": "Official page", "license_or_terms_note": "manual", "future_leakage_risk": "medium"}]},
            audit_report={"source_candidate_rows": [{"lane_name": "injuries_availability", "oxylabs_transport_used": "web_scraper_api", "oxylabs_calls_attempted": 1, "final_actionable_state": "manual_import_required"}]},
        )
        self.assertEqual(report["template_count"], 1)

    def test_build_all_returns_paths(self):
        fake_sample = {"source_result_index": {}, "sample_results": []}
        fake_inventory = {"fields_total": 1, "fields_missing_count": 0}
        fake_ledger = {"source_ledger_rows": [], "summary": {"free_open_populated": 0, "loader_ready_count": 0, "free_open_manual_import_needed": 0, "paid_data_subscription_required": 0, "blocked_reference_or_restricted_source": 0, "policy_blocked": 0, "license_terms_unclear": 0, "unavailable_after_max_effort": 0, "obsolete_or_duplicate": 0}}
        fake_schema = {"new_fields_created_count": 0, "new_tables_created_count": 0, "new_fields_created": [], "new_tables_created": []}
        fake_audit = {"source_candidate_rows": [], "source_candidate_count": 0, "lanes_tested_count": 0, "lanes_with_vague_status": 0, "oxylabs_residential_proxy_used": True, "oxylabs_web_scraper_api_used": True, "oxylabs_total_calls_attempted": 0, "oxylabs_total_calls_successful": 0, "oxylabs_total_calls_failed": 0, "lanes_improved_by_oxylabs": 0, "lanes_confirmed_paid_required": 0, "lanes_confirmed_manual_import_required": 0, "lanes_confirmed_policy_blocked": 0, "lanes_confirmed_terms_unclear": 0, "lanes_free_open_backfilled": 0, "lanes_loader_ready_hard_blocked_from_backfill": 0, "lanes_paid_subscription_required": 0, "lanes_manual_import_required": 0, "lanes_policy_blocked": 0, "lanes_license_terms_unclear": 0, "lanes_unavailable_after_exhaustive_free_search": 0, "lanes_obsolete_or_duplicate": 0}
        fake_backfill = {"loader_ready_lanes_before": 0, "loader_ready_lanes_backfilled": 0, "loader_ready_lanes_hard_blocked": 0, "records_added_by_soccer": 0, "fields_closed_this_pass": 0, "fields_partially_closed_this_pass": 0, "backfill_rows": []}
        fake_reclass = {"reclassification_row_count": 0, "reclassification_rows": []}
        fake_paid = {"requirement_rows": [], "paid_required_count": 0}
        fake_readiness = {"models": [{"recommendation": "manual_import_needed"}]}
        fake_manual = {"template_rows": [], "template_count": 0}
        fake_cert = {"free_open_exhaustion_verified": True}
        with ExitStack() as stack:
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_targeted_sample_verification_results", return_value=fake_sample))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_architecture_inventory", return_value=fake_inventory))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_free_vs_paid_source_ledger", return_value=fake_ledger))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_schema_expansion_report", return_value=fake_schema))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_oxylabs_source_exhaustion_log", return_value=fake_audit))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_loader_ready_backfill_report", return_value=fake_backfill))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_oxylabs_reclassification_report", return_value=fake_reclass))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_oxylabs_schema_expansion_report", return_value=fake_schema))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_paid_data_requirement_matrix", return_value=fake_paid))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_data_calibration_readiness_report", return_value=fake_readiness))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_manual_import_templates", return_value=fake_manual))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.build_soccer_free_open_exhaustion_certificate", return_value=fake_cert))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_architecture_inventory", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_free_vs_paid_source_ledger", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_targeted_sample_verification_results", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_schema_expansion_report", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_oxylabs_source_exhaustion_log", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_loader_ready_backfill_report", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_oxylabs_reclassification_report", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_oxylabs_schema_expansion_report", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_paid_data_requirement_matrix", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_data_calibration_readiness_report", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_free_open_exhaustion_certificate", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_manual_import_templates", return_value={"template_path": "x"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_manual_import_docs", return_value={"manual_import_docs_path": "y"}))
            stack.enter_context(patch("automation_scheduler.soccer_free_open_exhaustion.write_soccer_final_oxylabs_free_open_exhaustion_report", return_value={"latest_json_path": "a", "latest_markdown_path": "b"}))
            report = build_and_write_all_soccer_free_open_exhaustion_reports(tests_result="passed")
        self.assertTrue(report["ok"])
        self.assertIn("final", report["paths"])


if __name__ == "__main__":
    unittest.main()
