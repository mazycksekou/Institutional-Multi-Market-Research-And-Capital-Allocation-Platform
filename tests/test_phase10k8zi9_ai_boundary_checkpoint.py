from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZI9_AI_BOUNDARY_CHECKPOINT.md",
    ROOT / "POST_AI_BOUNDARY_ARCHITECTURE_MAP_AFTER_10K8ZI9.md",
    ROOT / "REMAINING_AI_ACTIVATION_QUEUE_AFTER_10K8ZI9.md",
    ROOT / "NEXT_BROKERAGE_EXECUTION_BOUNDARY_PLAN_AFTER_10K8ZI9.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_ai_checkpoint_docs_summarize_status() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "AI/LLM inventory complete",
        "src.ai",
        "disabled and local-only",
        "scheduler AI blockers are documented",
        "live AI/LLM activation",
        "prompt execution",
        "brokerage/live execution",
        "production deployment",
        "next brokerage/live execution boundary audit",
    ]:
        assert fragment.lower() in text.lower()


def test_ai_checkpoint_canonical_boundary_is_import_safe() -> None:
    import src.ai as ai

    assert ai.build_ai_readiness()["status"] == "deferred"
    assert ai.DisabledAIClient(reason="deferred").reason == "deferred"

