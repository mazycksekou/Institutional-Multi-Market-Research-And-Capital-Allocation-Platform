import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.services.streamlit_dashboard_facade import (
    AUTOMATION_DATA_DIR_ENV,
    RESEARCH_DATA_ROOT_ENV,
    get_automation_data_dir,
    get_calibration_reports_dir,
    get_collector_scheduler_dir,
    get_data_sources_dir,
    get_institutional_lab_dir,
    get_outcomes_dir,
    get_paper_ledger_dir,
    get_review_queue_dir,
    get_runtime_data_path,
    get_storage_health,
)


class TestDataPaths(unittest.TestCase):
    def test_research_data_root_is_used_when_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {RESEARCH_DATA_ROOT_ENV: tmp}, clear=True):
                self.assertEqual(get_automation_data_dir(), Path(tmp).resolve())
                self.assertEqual(get_runtime_data_path("outcomes"), Path(tmp).resolve() / "outcomes")

    def test_automation_data_dir_is_used_when_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                self.assertEqual(get_automation_data_dir(), Path(tmp).resolve())
                self.assertEqual(get_runtime_data_path("outcomes"), Path(tmp).resolve() / "outcomes")

    def test_local_data_fallback_when_env_missing_is_not_storage_ready(self):
        with patch.dict(os.environ, {}, clear=True):
            root = get_automation_data_dir()
            health = get_storage_health()
            self.assertEqual(root.name, "data")
            self.assertFalse(health["configured"])
            self.assertTrue(health["repo_local_fallback_active"])
            self.assertFalse(health["storage_ready"])
            self.assertIn("research_data_root_unconfigured", health["validation_errors"])
            self.assertIn(RESEARCH_DATA_ROOT_ENV, health["persistence_warning"])

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
                RESEARCH_DATA_ROOT_ENV: tmp,
                "RENDER": "",
                "RENDER_SERVICE_ID": "",
                "RENDER_EXTERNAL_HOSTNAME": "",
                "RENDER_INSTANCE_ID": "",
            }
            with patch.dict(os.environ, env, clear=True):
                health = get_storage_health()
        self.assertEqual(health["env_var"], RESEARCH_DATA_ROOT_ENV)
        self.assertEqual(health["canonical_env_var"], RESEARCH_DATA_ROOT_ENV)
        self.assertEqual(health["legacy_env_var"], AUTOMATION_DATA_DIR_ENV)
        self.assertEqual(health["configured_via_env_var"], RESEARCH_DATA_ROOT_ENV)
        self.assertEqual(health["backend"], "file")
        self.assertTrue(health["configured"])
        self.assertTrue(health["mount_ok"])
        self.assertTrue(health["read_ok"])
        self.assertTrue(health["write_ok"])
        self.assertTrue(health["free_space_ok"])
        self.assertTrue(health["repository_independent"])
        self.assertTrue(health["storage_ready"])
        self.assertTrue(health["migration_ready"])
        self.assertIsNone(health["persistence_warning"])

    def test_legacy_automation_data_dir_alias_remains_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {AUTOMATION_DATA_DIR_ENV: tmp}, clear=False):
                health = get_storage_health()
        self.assertEqual(health["env_var"], AUTOMATION_DATA_DIR_ENV)
        self.assertEqual(health["configured_via_env_var"], AUTOMATION_DATA_DIR_ENV)
        self.assertTrue(health["configured"])
        self.assertTrue(health["storage_ready"])


if __name__ == "__main__":
    unittest.main()
