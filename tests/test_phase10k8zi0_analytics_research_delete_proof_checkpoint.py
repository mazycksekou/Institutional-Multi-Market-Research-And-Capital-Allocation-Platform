from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZI0_ANALYTICS_RESEARCH_DELETE_PROOF_CHECKPOINT.md",
    ROOT / "POST_ANALYTICS_RESEARCH_DELETE_PROOF_ARCHITECTURE_MAP_AFTER_10K8ZI0.md",
    ROOT / "NEXT_ANALYTICS_RESEARCH_WRAPPER_DELETION_PLAN_AFTER_10K8ZI0.md",
]


def test_delete_proof_checkpoint_docs_state_current_decisions() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "wrapper delete-readiness",
        "remaining active blockers",
        "scheduler-coupled research blockers remain separate",
        "AI/LLM remains deferred",
        "brokerage/live execution remains deferred",
        "next recommended deletion or remediation phase",
    ]:
        assert fragment.lower() in text.lower()


def test_delete_proof_checkpoint_preserves_current_architecture() -> None:
    for relpath in [
        "src/analytics",
        "src/research",
        "model_governance",
        "automation_scheduler",
    ]:
        path = ROOT / relpath
        if relpath == "automation_scheduler":
            assert not path.exists()
        else:
            assert path.exists()
