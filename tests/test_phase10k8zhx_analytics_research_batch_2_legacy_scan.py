from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "ANALYTICS_RESEARCH_BATCH_2_LEGACY_IMPORT_SCAN_AFTER_10K8ZHX.md",
    ROOT / "ANALYTICS_RESEARCH_BATCH_2_REMAINING_BLOCKERS_AFTER_10K8ZHX.md",
    ROOT / "ANALYTICS_RESEARCH_BATCH_2_DELETE_READINESS_AFTER_10K8ZHX.md",
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
        "automation_scheduler/feature_ablation_lab.py",
        "automation_scheduler/calibration_strategy_filter.py",
        "automation_scheduler/experiment_history_store.py",
        "automation_scheduler/model_maturity_registry.py",
    ]:
        assert fragment in text


def test_legacy_files_are_not_deleted_and_canonical_packages_exist() -> None:
    for relpath in [
        "model_governance/governance_health.py",
        "model_governance/governance_report.py",
        "model_governance/model_validation_report.py",
        "automation_scheduler/deep_learning_research_lanes.py",
        "automation_scheduler/tabular_ml_research.py",
        "automation_scheduler/feature_ablation_lab.py",
        "automation_scheduler/calibration_strategy_filter.py",
        "automation_scheduler/experiment_history_store.py",
        "src/analytics/__init__.py",
        "src/research/__init__.py",
    ]:
        assert (ROOT / relpath).exists()
