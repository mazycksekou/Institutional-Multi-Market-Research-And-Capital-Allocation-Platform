from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pipeline_validation_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "PIPELINE_VALIDATION_AND_HARDENING_LAYER.md"
    report = DOCS / "reports" / "PHASE5_6_PIPELINE_VALIDATION_AND_HARDENING.md"
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

    assert "Pipeline Validation And Hardening Layer" in architecture_text
    assert "deterministic certification" in architecture_text.lower()
    assert "lineage completeness checks" in architecture_text.lower()
    assert "provenance integrity checks" in architecture_text.lower()
    assert "point-in-time correctness checks" in architecture_text.lower()
    assert "persisted validation artifacts" in architecture_text.lower()
    assert "dashboard-ready validation outputs" in architecture_text.lower()
    assert "research_intelligence_ready" in architecture_text
    assert "pipeline_validation_artifacts" in architecture_text

    assert "Phase 5.6 - Pipeline Validation And Hardening" in report_text
    assert "Canonical Owners Reused" in report_text
    assert "Implementation Summary" in report_text
    assert "Validation" in report_text
    assert "32 error-level checks" in report_text
    assert "Defects Found And Fixed" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text
    assert "Pipeline certified and ready for Research Intelligence." in report_text

    assert "Phase 5.7 - Research Intelligence" in project_status_text
    assert "Portable External Research-Data Storage" in project_status_text
    assert "docs/architecture/PIPELINE_VALIDATION_AND_HARDENING_LAYER.md" in project_status_text
    assert "docs/reports/PHASE5_6_PIPELINE_VALIDATION_AND_HARDENING.md" in project_status_text

    assert "NFL Production Completion" in next_action_text
    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "production-complete requirements" in next_action_text
    assert "Close only verified NFL production gaps" in next_action_text
    assert "certified and hardened NFL research pipeline" in next_action_text
    assert "Do not implement another sport." in next_action_text

    assert "Phase 5.6 completed pipeline validation and hardening on the production research engine path." in roadmap_text
    assert "Phase 5.7 completed deterministic Research Intelligence on top of the certified NFL pipeline." in roadmap_text

    assert "docs/architecture/PIPELINE_VALIDATION_AND_HARDENING_LAYER.md" in master_index_text
    assert "docs/architecture/PIPELINE_VALIDATION_AND_HARDENING_LAYER.md" in retention_index_text
    assert "docs/reports/PHASE5_6_PIPELINE_VALIDATION_AND_HARDENING.md" in retention_index_text

    assert "pipeline-validation-layer rollup" in p0_text.lower()
    assert "pipeline validation and hardening are complete in Phase 5.6" in p0_text
    assert "Research Intelligence is complete in Phase 5.7" in p0_text


def test_pipeline_validation_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "PIPELINE_VALIDATION_AND_HARDENING_LAYER.md"
    report = DOCS / "reports" / "PHASE5_6_PIPELINE_VALIDATION_AND_HARDENING.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "validation" in text.lower()
