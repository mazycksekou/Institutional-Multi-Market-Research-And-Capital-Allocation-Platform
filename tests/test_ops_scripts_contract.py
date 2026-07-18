import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestOpsScriptsContract(unittest.TestCase):
    def test_required_scripts_exist(self):
        for relative in (
            "scripts/ops_check.py",
            "scripts/run_quality_gates.py",
            "scripts/setup_dev.ps1",
            "scripts/check_local.ps1",
            "scripts/check_render.ps1",
            "scripts/check_cron.ps1",
            "scripts/check_all.ps1",
            "scripts/run_tests.ps1",
        ):
            self.assertTrue((ROOT / relative).exists(), relative)

    def test_run_tests_standardizes_pytest_and_explicit_unittest_fallback(self):
        script = (ROOT / "scripts/run_tests.ps1").read_text(encoding="utf-8")
        self.assertIn("python -m pytest", script)
        self.assertIn("FallbackUnittest", script)
        self.assertIn("python -m unittest discover", script)
        self.assertIn("tests/test_ops_workflow.py", script)

    def test_ops_check_exposes_required_modes(self):
        script = (ROOT / "scripts/ops_check.py").read_text(encoding="utf-8")
        for mode in ("local", "render", "cron", "calibration", "datasources", "safety", "full", "inventory", "import-scan"):
            self.assertIn(f'"{mode}"', script)
        for arg in ("--input", "--paths"):
            self.assertIn(arg, script)

    def test_repository_validation_workflow_uses_canonical_quality_gate(self):
        workflow = ROOT / ".github/workflows/repository-validation.yml"
        self.assertTrue(workflow.exists())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", text)
        self.assertIn('python-version: "3.12"', text)
        self.assertIn("main", text)
        self.assertIn("feature/nfl-backtesting", text)
        self.assertIn("feature/external-research-data-storage", text)
        self.assertIn("python scripts/run_quality_gates.py --install", text)

    def test_canonical_quality_gate_is_documented(self):
        expected = "./.venv/bin/python scripts/run_quality_gates.py --install"
        for relative in ("README.md", "docs/development/CONTRIBUTING.md", "scripts/setup_dev.ps1"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(expected, text, relative)

    def test_requirements_and_pytest_config_exist(self):
        self.assertTrue((ROOT / "requirements-dev.txt").exists())
        self.assertTrue((ROOT / "pytest.ini").exists())


if __name__ == "__main__":
    unittest.main()
