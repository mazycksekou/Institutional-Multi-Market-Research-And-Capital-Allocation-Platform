import unittest
from pathlib import Path

from scripts.check_document_lifecycle import collect_document_lifecycle_report


ROOT = Path(__file__).resolve().parents[1]


class TestDocumentLifecycleGovernance(unittest.TestCase):
    def test_document_lifecycle_policy_and_indexes_exist(self):
        policy = ROOT / "docs" / "architecture" / "DOCUMENT_LIFECYCLE_POLICY.md"
        checker = ROOT / "scripts" / "check_document_lifecycle.py"
        retention = ROOT / "docs" / "DOCUMENT_RETENTION_INDEX.md"
        master = ROOT / "docs" / "MASTER_DOCUMENT_INDEX.md"
        self.assertTrue(policy.exists())
        self.assertTrue(checker.exists())
        self.assertTrue(retention.exists())
        self.assertTrue(master.exists())

    def test_document_lifecycle_register_matches_current_tree(self):
        report = collect_document_lifecycle_report(ROOT)
        self.assertTrue(report["ok"])
        self.assertEqual(report["clear_violations"], [])
        self.assertEqual(report["root_markdown_offenders"], [])
        self.assertIn("docs/archive/historical_reports/CONTRACT_CONSISTENCY_REPORT.md", report["register_entries"])
        self.assertEqual(report["register_entries"]["docs/archive/historical_reports/CONTRACT_CONSISTENCY_REPORT.md"]["lifecycle_state"], "ARCHIVED")
        self.assertIn("docs/archive/milestones/REPOSITORY_MODERNIZATION_SUMMARY.md", report["register_entries"])
        self.assertEqual(report["register_entries"]["docs/archive/milestones/REPOSITORY_MODERNIZATION_SUMMARY.md"]["lifecycle_state"], "CONSOLIDATED")

    def test_ops_check_mentions_document_lifecycle_checker(self):
        ops_check = (ROOT / "scripts" / "ops_check.py").read_text(encoding="utf-8")
        self.assertIn("check_document_lifecycle.py", ops_check)
        self.assertIn("document_lifecycle", ops_check)

    def test_document_lifecycle_checker_is_python_native_and_workflow_does_not_install_ripgrep(self):
        checker = (ROOT / "scripts" / "check_document_lifecycle.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "repository-validation.yml").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", checker)
        self.assertNotIn('"rg"', checker)
        self.assertNotIn("ripgrep", workflow)
        self.assertNotIn("Install ripgrep", workflow)

    def test_docs_root_contains_only_retention_indexes(self):
        offenders = sorted(
            path.name
            for path in (ROOT / "docs").iterdir()
            if path.is_file() and path.suffix.lower() == ".md" and path.name not in {"DOCUMENT_RETENTION_INDEX.md", "MASTER_DOCUMENT_INDEX.md"}
        )
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
