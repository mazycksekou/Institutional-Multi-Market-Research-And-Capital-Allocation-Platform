from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_research_intelligence_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_INTELLIGENCE_LAYER.md"
    report = DOCS / "reports" / "PHASE5_7_RESEARCH_INTELLIGENCE.md"
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

    assert "Research Intelligence Layer" in architecture_text
    assert "certified nfl research pipeline" in architecture_text.lower()
    assert "evidence aggregation" in architecture_text.lower()
    assert "supporting evidence packages" in architecture_text.lower()
    assert "confidence explanations" in architecture_text.lower()
    assert "feature contribution summaries" in architecture_text.lower()
    assert "dashboard-ready research views" in architecture_text.lower()
    assert "research_intelligence_runs" in architecture_text
    assert "research_intelligence_opportunities" in architecture_text
    assert "research_intelligence_artifacts" in architecture_text
    assert "universal_market_framework_ready" in architecture_text

    assert "Phase 5.7 - Research Intelligence" in report_text
    assert "Canonical Owners Reused" in report_text
    assert "Implementation Summary" in report_text
    assert "Validation" in report_text
    assert "14 error-level checks" in report_text
    assert "2 wins, 1 loss, 0 pushes" in report_text
    assert "20.0% ROI" in report_text
    assert "Defects Found And Fixed" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text
    assert "ready for Universal Market Framework" in report_text

    assert "Phase 5.7 - Research Intelligence (complete)" in project_status_text
    assert "Universal Market Framework" in project_status_text
    assert "NFL Production Completion" in project_status_text
    assert "docs/architecture/RESEARCH_INTELLIGENCE_LAYER.md" in project_status_text
    assert "docs/reports/PHASE5_7_RESEARCH_INTELLIGENCE.md" in project_status_text

    assert "NFL Production Completion" in next_action_text
    assert "Universal Market Framework" in next_action_text
    assert "deterministic Research Intelligence layer" in next_action_text
    assert "Do not implement paper trading." in next_action_text
    assert "Do not implement live execution." in next_action_text

    assert "Phase 5.7 completed deterministic Research Intelligence on top of the certified NFL pipeline." in roadmap_text
    assert "The next governed step is the Universal Market Framework" in roadmap_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in roadmap_text

    assert "docs/architecture/RESEARCH_INTELLIGENCE_LAYER.md" in master_index_text
    assert "docs/architecture/RESEARCH_INTELLIGENCE_LAYER.md" in retention_index_text
    assert "docs/reports/PHASE5_7_RESEARCH_INTELLIGENCE.md" in retention_index_text

    assert "research-intelligence-layer rollup" in p0_text.lower()
    assert "Research Intelligence is complete in Phase 5.7" in p0_text
    assert "Universal Market Framework" in p0_text


def test_research_intelligence_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_INTELLIGENCE_LAYER.md"
    report = DOCS / "reports" / "PHASE5_7_RESEARCH_INTELLIGENCE.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "research intelligence" in text.lower()
