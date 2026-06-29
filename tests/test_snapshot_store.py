import unittest
from tempfile import TemporaryDirectory
from src.services.streamlit_dashboard_facade import get_default_scheduler_config
from src.services.streamlit_dashboard_facade import save_snapshot, load_latest_snapshot, diff_snapshots


class TestSnapshotStore(unittest.TestCase):
    def test_save_load_diff(self):
        with TemporaryDirectory() as tmp:
            c = get_default_scheduler_config(base_data_dir=tmp)
            a = save_snapshot("cat", "k", {"token": "x", "v": 1}, c)
            b = save_snapshot("cat", "k2", {"v": 2}, c)
            latest = load_latest_snapshot("cat", "k", c)
            self.assertEqual(latest["payload"]["token"], "[redacted]")
            self.assertTrue(diff_snapshots(a, b)["changed"])
