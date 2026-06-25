from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_completion_status() -> None:
    docs = (
        "PROJECT_COMPLETION_STATUS_AFTER_10K8ZK4.md",
        "ARCHITECTURE_EVOLUTION_SUMMARY_AFTER_10K8ZK4.md",
        "REMAINING_IMPLEMENTATION_BACKLOG_AFTER_10K8ZK4.md",
        "NEXT_OPERATOR_APPROVED_IMPLEMENTATION_PHASE_AFTER_10K8ZK4.md",
    )
    for name in docs:
        assert (ROOT / name).exists(), name

    completion_text = (ROOT / "PROJECT_COMPLETION_STATUS_AFTER_10K8ZK4.md").read_text(encoding="utf-8")
    for phrase in (
        "Completed migrations",
        "Canonical ownership",
        "Deleted wrappers",
        "Remaining implementation work",
        "Production readiness status",
        "Implementation backlog",
    ):
        assert phrase in completion_text

    backlog_text = (ROOT / "REMAINING_IMPLEMENTATION_BACKLOG_AFTER_10K8ZK4.md").read_text(encoding="utf-8")
    assert "broker adapter implementation" in backlog_text
    assert "deployment" in backlog_text.lower()
