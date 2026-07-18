from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_nfl_production_completion_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "NFL_PRODUCTION_COMPLETION.md"
    report = DOCS / "reports" / "PHASE5_8_NFL_PRODUCTION_COMPLETION.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"
    p0_architecture = DOCS / "architecture" / "NFL_P0_DATA_FOUNDATION.md"

    for path in (
        architecture_doc,
        report,
        project_status,
        next_action,
        master_index,
        retention_index,
        p0_architecture,
    ):
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)
    p0_text = _read(p0_architecture)

    assert "NFL Production Completion" in architecture_text
    assert "immutable reference behavior" in architecture_text.lower()
    assert "nfl_production_completion_runs" in architecture_text
    assert "nfl_production_completion_audit_items" in architecture_text
    assert "dashboard-ready production views" in architecture_text.lower()
    assert "query interfaces" in architecture_text.lower()
    assert "covariance_and_time_dependent_risk_audit_ready" in architecture_text

    assert "Phase 5.8 - NFL Production Completion" in report_text
    assert "Canonical Owners Reused" in report_text
    assert "NFL Production Audit Results" in report_text
    assert "16 error-level checks" in report_text
    assert "20.0% ROI" in report_text
    assert "Defects Found And Fixed" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text
    assert "No blocking NFL production gaps remain" in report_text

    assert "Data Identity, Reconciliation and Lakehouse Foundation" in project_status_text
    assert "First Controlled NFL Vendor Ingest" in project_status_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in project_status_text
    assert "Data Identity, Reconciliation and Lakehouse Foundation (complete)" in project_status_text
    assert "NFL Production Completion (complete)" in project_status_text
    assert "docs/architecture/NFL_PRODUCTION_COMPLETION.md" in project_status_text
    assert "docs/reports/PHASE5_8_NFL_PRODUCTION_COMPLETION.md" in project_status_text

    assert "Data Identity, Reconciliation and Lakehouse Foundation" in next_action_text
    assert "First Controlled NFL Vendor Ingest" in next_action_text
    assert "Portable External Research-Data Storage" in next_action_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in next_action_text
    assert "NFL Production Completion" in next_action_text
    assert "Universal Market Framework" in next_action_text
    assert "Activate only portable external research-data storage" in next_action_text
    assert "Do not implement covariance or the risk engine." in next_action_text
    assert "Do not implement paper trading." in next_action_text
    assert "Do not implement live execution." in next_action_text

    assert "NFL Production Completion is complete" in p0_text
    assert "Data Identity, Reconciliation and Lakehouse Foundation is complete" in p0_text
    assert "First Controlled NFL Vendor Ingest" in p0_text
    assert "Universal Market Framework" in p0_text

    assert "docs/architecture/NFL_PRODUCTION_COMPLETION.md" in master_index_text
    assert "docs/architecture/NFL_PRODUCTION_COMPLETION.md" in retention_index_text
    assert "docs/reports/PHASE5_8_NFL_PRODUCTION_COMPLETION.md" in retention_index_text


def test_nfl_production_completion_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "NFL_PRODUCTION_COMPLETION.md"
    report = DOCS / "reports" / "PHASE5_8_NFL_PRODUCTION_COMPLETION.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "nfl production completion" in text.lower()
