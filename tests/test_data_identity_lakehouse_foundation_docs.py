from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_data_identity_lakehouse_foundation_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = (
        DOCS / "architecture" / "DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md"
    )
    report = DOCS / "reports" / "PHASE5_9_DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"
    p0_architecture = DOCS / "architecture" / "NFL_P0_DATA_FOUNDATION.md"

    for path in (
        architecture_doc,
        report,
        project_status,
        next_action,
        roadmap,
        master_index,
        retention_index,
        p0_architecture,
    ):
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)
    p0_text = _read(p0_architecture)

    assert "Data Identity, Reconciliation And Lakehouse Foundation" in architecture_text
    assert "identity_mappings" in architecture_text
    assert "identity_reconciliation_results" in architecture_text
    assert "lakehouse_partitions" in architecture_text
    assert "data_identity_foundation_runs" in architecture_text
    assert "data_identity_foundation_audit_items" in architecture_text
    assert "first_controlled_nfl_vendor_ingest_ready" in architecture_text
    assert "Delta adoption" in architecture_text
    assert "manual-review routing" in architecture_text.lower()

    assert "Phase 5.9 - Data Identity, Reconciliation And Lakehouse Foundation" in report_text
    assert "Canonical Owners Reused" in report_text
    assert "Capability Audit Results" in report_text
    assert "22 stable identity mappings" in report_text
    assert "13 deterministic Bronze, Silver, and Gold Parquet partitions" in report_text
    assert "12 error-level checks" in report_text
    assert "Defects Found And Fixed" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text
    assert "No blocking data-identity or lakehouse blockers remain" in report_text

    assert "First Controlled NFL Vendor Ingest" in project_status_text
    assert "Data Identity, Reconciliation and Lakehouse Foundation (complete)" in project_status_text
    assert "docs/architecture/DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in project_status_text
    assert "docs/reports/PHASE5_9_DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in project_status_text

    assert "First Controlled NFL Vendor Ingest" in next_action_text
    assert "Portable External Research-Data Storage" in next_action_text
    assert "Data Identity, Reconciliation and Lakehouse Foundation" in next_action_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in next_action_text
    assert "Implement Confirmed Covariance And Time-Dependent Risk Gaps" in next_action_text
    assert "Dynamic and Point-in-Time Covariance" in next_action_text
    assert "Portfolio Exposure and Incremental Risk" in next_action_text
    assert "Time-Dependent Risk" in next_action_text
    assert "Historical Research-Chain Population" in next_action_text
    assert "Do not reimplement completed static covariance" in next_action_text
    assert "Do not create a parallel ingestion, storage, certification, lifecycle, identity, reconciliation, or retrieval framework." in next_action_text

    assert "The data identity foundation phase is complete and validated." in roadmap_text
    assert "The first controlled NFL vendor ingest phase must:" in roadmap_text
    assert "The portable external research-data storage phase must:" in roadmap_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in roadmap_text

    assert "docs/architecture/DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in master_index_text
    assert "docs/architecture/DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in retention_index_text
    assert "docs/reports/PHASE5_9_DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in retention_index_text

    assert "Data Identity, Reconciliation and Lakehouse Foundation rollup" in p0_text
    assert "First Controlled NFL Vendor Ingest" in p0_text


def test_data_identity_lakehouse_foundation_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = (
        DOCS / "architecture" / "DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md"
    )
    report = DOCS / "reports" / "PHASE5_9_DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "data identity" in text.lower()
