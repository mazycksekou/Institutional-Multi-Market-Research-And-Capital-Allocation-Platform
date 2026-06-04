import unittest
from pathlib import Path


class TestAutomationSchedulerScripts(unittest.TestCase):
    def test_scripts_exist_and_parse_text(self):
        p1 = Path("scripts/run_scheduler_once.ps1")
        p2 = Path("scripts/run_scheduler_health_check.ps1")
        p3 = Path("scripts/run_nfl_completion_backfill.ps1")
        p4 = Path("scripts/run_nfl_completion_report.ps1")
        p5 = Path("scripts/test_oxylabs_residential_proxy.ps1")
        p6 = Path("scripts/test_oxylabs_web_scraper_api.ps1")
        p7 = Path("scripts/run_mlb_completion_backfill.ps1")
        p8 = Path("scripts/run_mlb_completion_report.ps1")
        self.assertTrue(p1.exists())
        self.assertTrue(p2.exists())
        self.assertTrue(p3.exists())
        self.assertTrue(p4.exists())
        self.assertTrue(p5.exists())
        self.assertTrue(p6.exists())
        self.assertTrue(p7.exists())
        self.assertTrue(p8.exists())
        self.assertIn("python -c", p1.read_text(encoding="utf-8"))
        self.assertIn("python -c", p2.read_text(encoding="utf-8"))
        self.assertIn("automation_scheduler.nfl_completion_backfill", p3.read_text(encoding="utf-8"))
        self.assertIn("automation_scheduler.nfl_completion_report", p4.read_text(encoding="utf-8"))
        self.assertIn("pytest", p5.read_text(encoding="utf-8"))
        self.assertIn("pytest", p6.read_text(encoding="utf-8"))
        self.assertIn("automation_scheduler.mlb_completion_backfill", p7.read_text(encoding="utf-8"))
        self.assertIn("automation_scheduler.mlb_completion_report", p8.read_text(encoding="utf-8"))
