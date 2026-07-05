import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestAutomationSchedulerScripts(unittest.TestCase):
    def test_python_equivalents_exist_and_wrappers_delegate_to_python(self):
        expected_python_scripts = (
            "scripts/run_scheduler_once.py",
            "scripts/run_scheduler_health_check.py",
            "scripts/run_json_audit_pipeline.py",
            "scripts/install_json_audit_scheduled_task.py",
            "scripts/uninstall_json_audit_scheduled_task.py",
            "scripts/export_kalshi_local_outcomes.py",
            "scripts/dry_run_import_kalshi_outcomes.py",
            "scripts/persist_import_kalshi_outcomes.py",
            "scripts/review_json_audit_with_deepseek.py",
        )
        for relative in expected_python_scripts:
            self.assertTrue((ROOT / relative).exists(), relative)

        wrapper_expectations = {
            "scripts/run_scheduler_once.ps1": "run_scheduler_once.py",
            "scripts/run_scheduler_health_check.ps1": "run_scheduler_health_check.py",
            "scripts/run_json_audit_pipeline.ps1": "run_json_audit_pipeline.py",
            "scripts/install_json_audit_scheduled_task.ps1": "install_json_audit_scheduled_task.py",
            "scripts/uninstall_json_audit_scheduled_task.ps1": "uninstall_json_audit_scheduled_task.py",
            "scripts/export_kalshi_local_outcomes.ps1": "export_kalshi_local_outcomes.py",
            "scripts/dry_run_import_kalshi_outcomes.ps1": "dry_run_import_kalshi_outcomes.py",
            "scripts/persist_import_kalshi_outcomes.ps1": "persist_import_kalshi_outcomes.py",
            "scripts/review_json_audit_with_deepseek.ps1": "review_json_audit_with_deepseek.py",
        }
        for relative, expected in wrapper_expectations.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("python", text, relative)
            self.assertIn(expected, text, relative)

        daily_hygiene = (ROOT / "scripts/run_daily_data_hygiene.ps1").read_text(encoding="utf-8")
        self.assertIn("python scripts/daily_data_hygiene.py", daily_hygiene)
        self.assertIn("--execute --upload --verify --cleanup --allow-delete-local-raw", daily_hygiene)

        ai_ps1 = (ROOT / "ai.ps1").read_text(encoding="utf-8")
        self.assertIn("Set-Location $PSScriptRoot", ai_ps1)
        self.assertNotIn("C:\\Users\\user\\betting-stock-api-code-integration", ai_ps1)

    def test_run_tests_standardizes_pytest_and_explicit_unittest_fallback(self):
        script = (ROOT / "scripts/run_tests.ps1").read_text(encoding="utf-8")
        self.assertIn("python -m pytest", script)
        self.assertIn("FallbackUnittest", script)
        self.assertIn("python -m unittest discover", script)
        self.assertIn("tests/test_ops_workflow.py", script)


if __name__ == "__main__":
    unittest.main()
