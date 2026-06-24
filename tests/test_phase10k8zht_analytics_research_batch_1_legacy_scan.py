from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "ANALYTICS_RESEARCH_BATCH_1_LEGACY_IMPORT_SCAN_AFTER_10K8ZHT.md",
    ROOT / "ANALYTICS_RESEARCH_BATCH_1_REMAINING_BLOCKERS_AFTER_10K8ZHT.md",
    ROOT / "ANALYTICS_RESEARCH_BATCH_1_NEXT_SEQUENCE_AFTER_10K8ZHT.md",
]


def test_legacy_scan_docs_include_expected_blocker_categories() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "MODEL_GOVERNANCE_ENFORCEMENT_BLOCKED",
        "AI_ADJACENT_BLOCKED",
        "SCHEDULER_COUPLED_BLOCKED",
        "FILE_IO_OR_STORAGE_BLOCKED",
        "TRAINING_OR_EXECUTION_BLOCKED",
        "SAFE_FOR_LATER_COMPATIBILITY_SHIM",
        "DELETE_CANDIDATE_AFTER_PROOF",
        "model_governance/governance_health.py",
        "automation_scheduler/deepseek_daily_report.py",
        "research/market_research_schema.py",
    ]:
        assert fragment in text


def test_legacy_files_are_not_deleted_and_canonical_packages_exist() -> None:
    for relpath in [
        "src/analytics/__init__.py",
        "src/research/__init__.py",
        "src/analytics/governance.py",
        "src/research/storage.py",
    ]:
        assert (ROOT / relpath).exists()
