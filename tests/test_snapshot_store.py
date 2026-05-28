import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.scheduler_config import get_default_scheduler_config
from automation_scheduler.snapshot_store import SnapshotStore


class TestSnapshotStore(unittest.TestCase):
    def test_save_load_and_diff_snapshots(self):
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            store = SnapshotStore(config)
            first = store.save_snapshot("odds", "run1", {"price": 100, "api_key": "secret"})
            second = store.save_snapshot("odds", "run2", {"price": 101})
            loaded = store.load_snapshot("odds", "run1")
            diff = SnapshotStore.diff_snapshots(first, second)
            self.assertEqual(loaded["payload"]["api_key"], "[redacted]")
            self.assertTrue(diff["changed"])
            self.assertIn("price", diff["changed_keys"])
