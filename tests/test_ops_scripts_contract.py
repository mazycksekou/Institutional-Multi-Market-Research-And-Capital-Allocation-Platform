import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestOpsScriptsContract(unittest.TestCase):
    def test_required_scripts_exist(self):
        for relative in (
            "scripts/ops_check.py",
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
        for mode in ("local", "render", "cron", "calibration", "datasources", "safety", "full"):
            self.assertIn(f'"{mode}"', script)

    def test_docs_file_exists(self):
        docs = ROOT / "docs/OPS_WORKFLOW.md"
        self.assertTrue(docs.exists())
        text = docs.read_text(encoding="utf-8")
        self.assertIn(".\\scripts\\check_local.ps1", text)
        self.assertIn("Codex should use these scripts", text)

    def test_requirements_and_pytest_config_exist(self):
        self.assertTrue((ROOT / "requirements-dev.txt").exists())
        self.assertTrue((ROOT / "pytest.ini").exists())


if __name__ == "__main__":
    unittest.main()

