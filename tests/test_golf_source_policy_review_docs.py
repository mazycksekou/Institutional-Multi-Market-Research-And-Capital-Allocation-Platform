import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfSourcePolicyReviewDocs(unittest.TestCase):
    def test_policy_review_document_is_written(self):
        path = golf_artifacts()["policy_docs_path"]
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("Golf Source Policy Review", text)
        self.assertIn("OpenGolfAPI course dataset", text)


if __name__ == "__main__":
    unittest.main()
