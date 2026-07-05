from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "docs" / "archive" / "milestones" / "LEGACY_CLEANUP_SUMMARY.md"
RETENTION_INDEX = ROOT / "docs" / "DOCUMENT_RETENTION_INDEX.md"


def test_phase10k8zk7_runtime_redirection_docs_exist() -> None:
    summary = SUMMARY.read_text(encoding="utf-8")
    retention = RETENTION_INDEX.read_text(encoding="utf-8")

    for fragment in [
        "AUTOMATION_SCHEDULER_RUNTIME_REDIRECTION_MAP_AFTER_10K8ZK7.md",
        "Execution cleanup snapshots",
        "Deleted In This Pass",
    ]:
        assert fragment in summary

    assert "docs/archive/milestones/legacy_cleanup_summary.md" in retention.lower()
    assert "consolidated" in retention.lower()
