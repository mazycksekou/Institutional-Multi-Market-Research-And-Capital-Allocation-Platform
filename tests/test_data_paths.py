import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.services.streamlit_dashboard_facade import AUTOMATION_DATA_DIR_ENV, get_automation_data_dir, get_calibration_reports_dir, get_collector_scheduler_dir, get_data_sources_dir, get_institutional_lab_dir, get_outcomes_dir, get_paper_ledger_dir, get_review_queue_dir, get_runtime_data_path, get_storage_health


class TestDataPaths(unittest.TestCase):
    def test_automation_data_dir_is_used_when_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                self.assertEqual(get_automation_data_dir(), Path(tmp).resolve())
                self.assertEqual(get_runtime_data_path("outcomes"), Path(tmp).resolve() / "outcomes")

    def test_local_data_fallback_when_env_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            root = get_automation_data_dir()
            self.assertEqual(root.name, "data")
            self.assertTrue(root.exists())

    def test_runtime_dirs_resolve_under_automation_data_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: str(root)}, clear=False):
                expected = {
                    get_review_queue_dir(): "review_queue",
                    get_paper_ledger_dir(): "paper_ledger",
                    get_outcomes_dir(): "outcomes",
                    get_collector_scheduler_dir(): "collector_scheduler",
                    get_institutional_lab_dir(): "institutional_lab",
                    get_data_sources_dir(): "data_sources",
                    get_calibration_reports_dir(): "calibration",
                }
                for path, suffix in expected.items():
                    self.assertEqual(path, root / suffix)
                    self.assertEqual(path.resolve().relative_to(root), Path(suffix))

    def test_runtime_path_rejects_absolute_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                with self.assertRaises(ValueError):
                    get_runtime_data_path(Path(tmp).resolve())

    def test_storage_health_reports_env_var_and_smoke_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                AUTOMATION_DATA_DIR_ENV: tmp,
                "RENDER": "",
                "RENDER_SERVICE_ID": "",
                "RENDER_EXTERNAL_HOSTNAME": "",
                "RENDER_INSTANCE_ID": "",
            }
            with patch.dict(os.environ, env, clear=False):
                health = get_storage_health()
        self.assertEqual(health["env_var"], "AUTOMATION_DATA_DIR")
        self.assertEqual(health["backend"], "file")
        self.assertTrue(health["configured"])
        self.assertTrue(health["read_ok"])
        self.assertTrue(health["write_ok"])
        self.assertIsNone(health["persistence_warning"])


if __name__ == "__main__":
    unittest.main()
