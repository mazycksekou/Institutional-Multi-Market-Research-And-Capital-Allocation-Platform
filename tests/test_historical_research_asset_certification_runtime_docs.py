from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_historical_research_asset_certification_runtime_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md"
    report = DOCS / "reports" / "PHASE4_7C_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in [architecture_doc, report, project_status, next_action, master_index, retention_index]:
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "Historical Research Asset Certification Runtime" in architecture_text
    assert "research asset certification" in architecture_text.lower()
    assert "dataset certification" in architecture_text.lower()
    assert "Certification States" in architecture_text
    assert "Certification Failure Reasons" in architecture_text
    assert "Multi-Provider Support" in architecture_text
    assert "Readiness Reporting" in architecture_text
    assert "Phase 4.7C completes the historical research asset certification runtime" in architecture_text
    assert "Phase 4.9A populates the NFL schedule research asset" in architecture_text

    assert "Phase 4.7C Historical Research Asset Certification Runtime" in report_text
    assert "Existing Certification Abstractions Discovered" in report_text
    assert "Existing Abstractions Reused" in report_text
    assert "Runtime Delivered" in report_text
    assert "Certification State Coverage" in report_text
    assert "Failure Reason Coverage" in report_text
    assert "Multi-Provider Support" in report_text
    assert "Engineering Improvements Implemented" in report_text
    assert "Engineering Improvements Deferred" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview Intelligence Review" in report_text
    assert "Readiness for Phase 4.8" in report_text

    assert "Phase 4.7C - Historical Research Asset Certification Runtime" in project_status_text
    assert "Phase 4.9A - NFL Schedule Research Asset Population" in project_status_text
    assert "Phase 4.9B - Research Asset Coverage Planner & Provider Selection Framework" in project_status_text
    assert "Phase 4.9C - First Production Connector (NFL Schedule)" in project_status_text
    assert "Phase 4.9D - NFL Results Research Asset Population" in project_status_text
    assert "Phase 4.9E - NFL Odds Research Asset Population" in project_status_text
    assert "docs/architecture/HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md" in project_status_text
    assert "docs/reports/PHASE4_7C_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md" in project_status_text
    assert "Phase 5.3 - Reusable Signals" in next_action_text

    assert "docs/architecture/HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md" in master_index_text
    assert "docs/reports/PHASE4_7C_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md" in retention_index_text


def test_historical_research_asset_certification_runtime_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md"
    report = DOCS / "reports" / "PHASE4_7C_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "certification" in text.lower()
