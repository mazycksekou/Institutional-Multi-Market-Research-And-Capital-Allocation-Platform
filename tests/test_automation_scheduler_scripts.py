import unittest
from pathlib import Path


class TestAutomationSchedulerScripts(unittest.TestCase):
    def test_scripts_exist_and_parse_text(self):
        p1 = Path("scripts/run_scheduler_once.ps1")
        p2 = Path("scripts/run_scheduler_health_check.ps1")
        self.assertTrue(p1.exists())
        self.assertTrue(p2.exists())
        self.assertIn("python -c", p1.read_text(encoding="utf-8"))
        self.assertIn("python -c", p2.read_text(encoding="utf-8"))
