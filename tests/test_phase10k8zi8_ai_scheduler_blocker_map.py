from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "AI_SCHEDULER_BLOCKER_MAP_AFTER_10K8ZI8.md",
    ROOT / "AI_SCHEDULER_MIGRATION_SEQUENCE_AFTER_10K8ZI8.md",
    ROOT / "AI_SCHEDULER_DELETE_READINESS_AFTER_10K8ZI8.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_scheduler_blocker_docs_capture_requested_categories() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "AI_RUNTIME_CALL_RISK",
        "AI_CREDENTIAL_RISK",
        "SCHEDULER_COUPLED_BLOCKED",
        "PROMPT_TEMPLATE_ONLY",
        "RESEARCH_METADATA_ONLY",
        "MIGRATE_TO_SRC_AI_LATER",
        "MIGRATE_TO_SRC_SERVICES_LATER",
        "DELETE_CANDIDATE_AFTER_PROOF",
        "automation_scheduler/deepseek_reviewer.py",
        "automation_scheduler/deepseek_profit_lab.py",
        "automation_scheduler/institutional_deepseek_review.py",
        "automation_scheduler/ai_provider_security.py",
    ]:
        assert fragment.lower() in text.lower()


def test_scheduler_blocker_docs_state_no_activation() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "no scheduler activation occurred in this phase",
        "automation_scheduler remains a decommission target",
        "no ai/llm calls occurred",
        "no deletion occurred",
    ]:
        assert fragment.lower() in text.lower()

