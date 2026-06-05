import csv
import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfManualImportTemplates(unittest.TestCase):
    def test_manual_template_and_docs_exist(self):
        artifacts = golf_artifacts()
        self.assertTrue(artifacts["manual_template_path"].exists())
        self.assertTrue(artifacts["manual_docs_path"].exists())
        with artifacts["manual_template_path"].open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertGreater(len(rows), 0)
        self.assertIn("source_url_hash_required", rows[0])


if __name__ == "__main__":
    unittest.main()
