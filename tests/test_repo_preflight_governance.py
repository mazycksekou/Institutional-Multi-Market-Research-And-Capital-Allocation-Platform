import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_repo_preflight as preflight


ROOT = Path(__file__).resolve().parents[1]


def _clean_git_state(*, branch: str = "feature/external-research-data-storage") -> dict[str, object]:
    return {
        "branch": branch,
        "head": "deadbeef1234567890",
        "upstream": f"origin/{branch}",
        "ahead": 0,
        "behind": 0,
        "staged_files": [],
        "modified_files": [],
        "untracked_files": [],
        "status_summary": f"## {branch}...origin/{branch}",
    }


class TestRepoPreflightGovernance(unittest.TestCase):
    def test_policy_and_script_exist(self) -> None:
        script = ROOT / "scripts" / "check_repo_preflight.py"
        policy = ROOT / "docs" / "development" / "BRANCH_GOVERNANCE_POLICY.md"
        self.assertTrue(script.exists())
        self.assertTrue(policy.exists())

    def test_clean_state_report_is_ok(self) -> None:
        with (
            patch.object(preflight, "_git_state", return_value=_clean_git_state()),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
        ):
            report = preflight.collect_repo_preflight_report(ROOT, mode="start-task", include_ops=False)

        self.assertTrue(report["ok"])
        self.assertEqual(report["clear_violations"], [])
        self.assertTrue(report["working_tree_clean"])
        self.assertTrue(report["index_clean"])
        self.assertEqual(report["branch"], "feature/external-research-data-storage")
        self.assertEqual(report["upstream"], "origin/feature/external-research-data-storage")
        self.assertEqual(report["checks"]["root_markdown"]["status"], "ok")

    def test_clean_state_report_accepts_main_after_merge(self) -> None:
        with (
            patch.object(preflight, "_git_state", return_value=_clean_git_state(branch="main")),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
        ):
            report = preflight.collect_repo_preflight_report(ROOT, mode="start-task", include_ops=False)

        self.assertTrue(report["ok"])
        self.assertEqual(report["branch"], "main")
        self.assertEqual(report["upstream"], "origin/main")

    def test_clean_state_report_accepts_external_storage_branch(self) -> None:
        with (
            patch.object(preflight, "_git_state", return_value=_clean_git_state(branch="feature/external-research-data-storage")),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
        ):
            report = preflight.collect_repo_preflight_report(ROOT, mode="start-task", include_ops=False)

        self.assertTrue(report["ok"])
        self.assertEqual(report["branch"], "feature/external-research-data-storage")
        self.assertEqual(report["upstream"], "origin/feature/external-research-data-storage")

    def test_clean_state_report_accepts_feature_nfl_branch(self) -> None:
        with (
            patch.object(preflight, "_git_state", return_value=_clean_git_state(branch="feature/nfl-backtesting")),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
        ):
            report = preflight.collect_repo_preflight_report(ROOT, mode="start-task", include_ops=False)

        self.assertTrue(report["ok"])
        self.assertEqual(report["branch"], "feature/nfl-backtesting")
        self.assertEqual(report["upstream"], "origin/feature/nfl-backtesting")

    def test_dirty_state_is_reported_as_clear_violation(self) -> None:
        dirty_state = _clean_git_state()
        dirty_state["modified_files"] = ["docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md"]
        dirty_state["untracked_files"] = ["docs/temporary_note.md"]

        with (
            patch.object(preflight, "_git_state", return_value=dirty_state),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
        ):
            report = preflight.collect_repo_preflight_report(ROOT, mode="before-commit", include_ops=False)

        self.assertFalse(report["ok"])
        self.assertTrue(any("working tree is not clean" in item for item in report["clear_violations"]))

    def test_before_commit_accepts_staged_changes_when_worktree_is_clean(self) -> None:
        staged_state = _clean_git_state()
        staged_state["staged_files"] = ["docs/architecture/BRANCH_GOVERNANCE_POLICY.md"]

        with (
            patch.object(preflight, "_git_state", return_value=staged_state),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
        ):
            report = preflight.collect_repo_preflight_report(ROOT, mode="before-commit", include_ops=False)

        self.assertTrue(report["ok"])
        self.assertFalse(report["index_clean"])
        self.assertTrue(report["working_tree_clean"])

    def test_before_push_requires_ahead_of_upstream(self) -> None:
        push_state = _clean_git_state()
        push_state["ahead"] = 1

        with (
            patch.object(preflight, "_git_state", return_value=push_state),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
        ):
            report = preflight.collect_repo_preflight_report(ROOT, mode="before-push", include_ops=False)

        self.assertTrue(report["ok"])
        self.assertEqual(report["ahead"], 1)
        self.assertEqual(report["behind"], 0)

    def test_optional_ops_validation_is_included_when_requested(self) -> None:
        with (
            patch.object(preflight, "_git_state", return_value=_clean_git_state()),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_ops", return_value={"blocker_classification": {"primary": "ok", "recommended_action": "continue"}}),
        ):
            report = preflight.collect_repo_preflight_report(ROOT, mode="end-task", include_ops=True)

        self.assertIn("ops", report["checks"])
        self.assertEqual(report["checks"]["ops"]["blocker_classification"]["primary"], "ok")

    def test_ops_check_mentions_repo_preflight_checker(self) -> None:
        ops_check = (ROOT / "scripts" / "ops_check.py").read_text(encoding="utf-8")
        self.assertIn("check_repo_preflight.py", ops_check)
        self.assertIn("repo_preflight", ops_check)

    def test_cli_accepts_start_task_flag(self) -> None:
        with (
            patch.object(preflight, "_git_state", return_value=_clean_git_state()),
            patch.object(preflight, "_check_root_markdown", return_value={"status": "ok", "offenders": []}),
            patch.object(preflight, "_check_openapi", return_value={"ok": True, "errors": []}),
            patch.object(preflight, "_check_architecture", return_value={"root_markdown_offenders": [], "ignored_source_files": [], "legacy_import_issues": []}),
            patch.object(preflight, "_check_audit_lifecycle", return_value={"clear_violations": []}),
            patch.object(preflight, "_check_document_lifecycle", return_value={"clear_violations": []}),
        ):
            exit_code = preflight.main(["--start-task"])

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
