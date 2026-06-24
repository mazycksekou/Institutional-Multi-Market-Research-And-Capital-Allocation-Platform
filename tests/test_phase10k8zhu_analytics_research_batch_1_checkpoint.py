from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHU_ANALYTICS_RESEARCH_BATCH_1_CHECKPOINT.md",
    ROOT / "POST_ANALYTICS_RESEARCH_BATCH_1_ARCHITECTURE_MAP_AFTER_10K8ZHU.md",
    ROOT / "NEXT_ANALYTICS_RESEARCH_BATCH_2_PLAN_AFTER_10K8ZHU.md",
]


def test_checkpoint_docs_state_batch_1_and_next_step() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "analytics migration status",
        "research migration status",
        "legacy preservation status",
        "remaining blockers",
        "why AI/LLM remains deferred",
        "why brokerage/live execution remains deferred",
        "next recommended Batch 2",
    ]:
        assert fragment.lower() in text.lower()


def test_checkpoint_package_paths_exist() -> None:
    for relpath in [
        "src/analytics",
        "src/research",
        "model_governance",
        "research",
    ]:
        assert (ROOT / relpath).exists()

