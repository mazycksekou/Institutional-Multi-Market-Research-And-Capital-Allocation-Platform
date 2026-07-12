from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_research_asset_lifecycle_runtime_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_ASSET_LIFECYCLE_RUNTIME.md"
    report = DOCS / "reports" / "PHASE4_8_RESEARCH_ASSET_LIFECYCLE_RUNTIME_AND_TIME_ENTITY_ALIGNMENT_CERTIFICATION.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    master_roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in [architecture_doc, report, project_status, next_action, master_roadmap, master_index, retention_index]:
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(master_roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "Research Asset Lifecycle Runtime" in architecture_text
    assert "Time & Entity Alignment Certification" in architecture_text
    assert "Immutable Research Asset Identity" in architecture_text
    assert "Research Asset Lifecycle" in architecture_text
    assert "DISCOVERED" in architecture_text
    assert "SOURCE_IDENTIFIED" in architecture_text
    assert "CONNECTOR_MAPPED" in architecture_text
    assert "DATASET_CERTIFIED" in architecture_text
    assert "FEATURE_READY" in architecture_text
    assert "BACKTEST_READY" in architecture_text
    assert "ENTITY_MISMATCH" in architecture_text
    assert "POINT_IN_TIME_VIOLATION" in architecture_text
    assert "multi-provider" in architecture_text.lower()
    assert "Worldview" in architecture_text

    assert "Phase 4.8 - Research Asset Lifecycle Runtime & Time & Entity Alignment Certification" in report_text
    assert "Existing Lifecycle Abstractions Discovered" in report_text
    assert "Existing Abstractions Reused" in report_text
    assert "Research Asset Lifecycle Runtime Implemented" in report_text
    assert "Immutable Research Asset Identity" in report_text
    assert "Time & Entity Alignment Certification" in report_text
    assert "Certification Pipeline Updated" in report_text
    assert "Engineering Improvements Implemented" in report_text
    assert "Engineering Improvements Deferred" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview Intelligence Review" in report_text
    assert "Readiness for Phase 4.9" in report_text

    assert "Phase 4.9A - NFL Schedule Research Asset Population" in project_status_text
    assert "Phase 4.9B - Research Asset Coverage Planner & Provider Selection Framework" in project_status_text
    assert "Phase 4.9C - First Production Connector (NFL Schedule)" in project_status_text
    assert "Phase 4.9F - NFL Weather Research Asset Population" in project_status_text
    assert "docs/architecture/RESEARCH_ASSET_LIFECYCLE_RUNTIME.md" in project_status_text
    assert "docs/reports/PHASE4_8_RESEARCH_ASSET_LIFECYCLE_RUNTIME_AND_TIME_ENTITY_ALIGNMENT_CERTIFICATION.md" in project_status_text
    assert "Phase 5.3 - Reusable Signals" in next_action_text
    assert "Do not implement connectors." in next_action_text
    assert "canonical open-provider acquisition path" in next_action_text.lower()

    assert "Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification." in roadmap_text
    assert "Phase 4.9A populates the NFL schedule research asset." in roadmap_text
    assert "Phase 4.9B builds the research asset coverage planner and provider selection framework." in roadmap_text
    assert "Phase 4.9C implements the first production connector for the NFL schedule research asset." in roadmap_text
    assert "Phase 5.0 completed the historical dataset population layer" in roadmap_text
    assert "Phase 5.1B completed the reusable feature snapshot population layer" in roadmap_text
    assert "Phase 5.2 completed reusable mathematical engines." in roadmap_text
    assert "Phase 5.3 implements reusable signals." in roadmap_text
    assert "Phase 5.4 generates decision rows from events, markets, selections, and feature snapshots." in roadmap_text
    assert "Phase 5.5 begins baseline backtesting from frozen, certified inputs." in roadmap_text
    assert "Phase 5.6 performs validation and hardening on the production research engine path." in roadmap_text

    assert "docs/architecture/RESEARCH_ASSET_LIFECYCLE_RUNTIME.md" in master_index_text
    assert "docs/reports/PHASE4_8_RESEARCH_ASSET_LIFECYCLE_RUNTIME_AND_TIME_ENTITY_ALIGNMENT_CERTIFICATION.md" in retention_index_text


def test_research_asset_lifecycle_runtime_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_ASSET_LIFECYCLE_RUNTIME.md"
    report = DOCS / "reports" / "PHASE4_8_RESEARCH_ASSET_LIFECYCLE_RUNTIME_AND_TIME_ENTITY_ALIGNMENT_CERTIFICATION.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "lifecycle" in text.lower()
