from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_historical_dataset_acquisition_runtime_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "HISTORICAL_DATASET_ACQUISITION_RUNTIME.md"
    report = DOCS / "reports" / "PHASE4_7B_HISTORICAL_DATASET_ACQUISITION_RUNTIME.md"
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

    assert "Historical Dataset Acquisition Runtime" in architecture_text
    assert "raw acquisition cache staging" in architecture_text.lower()
    assert "integrity validation" in architecture_text.lower()
    assert "normalization/certification handoff" in architecture_text.lower()
    assert "multi-provider" in architecture_text.lower()
    assert "Phase 4.7B builds the reusable historical dataset acquisition runtime" in architecture_text
    assert "Phase 4.7C completes the historical research asset certification runtime" in architecture_text

    assert "Phase 4.7B Historical Dataset Acquisition Runtime" in report_text
    assert "Raw Acquisition Cache Implemented" in report_text
    assert "Integrity Validation Implemented" in report_text
    assert "Normalization Interfaces Implemented" in report_text
    assert "Certification Interfaces Implemented" in report_text
    assert "Shared Logic Reused" in report_text
    assert "Duplicate Logic Avoided" in report_text
    assert "Readiness for Phase 4.7C" in report_text

    assert "Phase 4.7C - Historical Research Asset Certification Runtime" in project_status_text
    assert "Phase 4.8 - Research Asset Lifecycle Runtime & Time & Entity Alignment Certification" in project_status_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_RUNTIME.md" in project_status_text
    assert "docs/reports/PHASE4_7B_HISTORICAL_DATASET_ACQUISITION_RUNTIME.md" in project_status_text
    assert "Phase 4.9F - NFL Weather Research Asset Population" in next_action_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_RUNTIME.md" in master_index_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_RUNTIME.md" in retention_index_text
    assert "docs/reports/PHASE4_7B_HISTORICAL_DATASET_ACQUISITION_RUNTIME.md" in retention_index_text


def test_historical_dataset_acquisition_runtime_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "HISTORICAL_DATASET_ACQUISITION_RUNTIME.md"
    report = DOCS / "reports" / "PHASE4_7B_HISTORICAL_DATASET_ACQUISITION_RUNTIME.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "raw acquisition cache" in text.lower()
