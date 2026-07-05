from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHY_ANALYTICS_RESEARCH_BATCH_2_CHECKPOINT.md",
    ROOT / "POST_ANALYTICS_RESEARCH_BATCH_2_ARCHITECTURE_MAP_AFTER_10K8ZHY.md",
    ROOT / "NEXT_ANALYTICS_RESEARCH_DELETE_PROOF_PLAN_AFTER_10K8ZHY.md",
]


def test_checkpoint_docs_state_batch_2_and_next_step() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "analytics downstream redirection status",
        "research downstream redirection status",
        "legacy preservation status",
        "remaining blockers",
        "why AI/LLM remains deferred",
        "why brokerage/live execution remains deferred",
        "next recommended delete-proof phase",
    ]:
        assert fragment.lower() in text.lower()


def test_checkpoint_package_paths_exist() -> None:
    for relpath in [
        "src/analytics",
        "src/research",
        "model_governance",
        "automation_scheduler",
        "research",
    ]:
        path = ROOT / relpath
        if relpath == "automation_scheduler":
            assert not path.exists()
        else:
            assert path.exists()
