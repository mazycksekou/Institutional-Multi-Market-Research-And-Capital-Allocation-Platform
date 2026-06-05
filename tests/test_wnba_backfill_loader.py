import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation_scheduler.wnba_backfill_loader import build_and_write_wnba_backfill_loader_report, build_wnba_backfill_loader_report


class TestWnbaBackfillLoader(unittest.TestCase):
    def test_build_wrapper_forwards_sport(self):
        with patch(
            "automation_scheduler.wnba_backfill_loader.build_basketball_loader_ready_backfill_report",
            return_value={"ok": True, "sport": "basketball_wnba"},
        ) as build_mock:
            report = build_wnba_backfill_loader_report()
        build_mock.assert_called_once_with(sport="basketball_wnba")
        self.assertEqual(report["sport"], "basketball_wnba")

    def test_build_and_write_wrapper_forwards_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
            "automation_scheduler.wnba_backfill_loader.build_and_write_basketball_loader_ready_backfill_report",
            return_value={"ok": True, "sport": "basketball_wnba"},
        ) as build_write_mock:
            report = build_and_write_wnba_backfill_loader_report(output_dir=Path(tmp) / "reports")
        build_write_mock.assert_called_once_with(sport="basketball_wnba", output_dir=Path(tmp) / "reports")
        self.assertEqual(report["sport"], "basketball_wnba")


if __name__ == "__main__":
    unittest.main()
