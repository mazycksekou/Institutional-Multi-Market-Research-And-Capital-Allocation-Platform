from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_research_asset_coverage_planner_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_ASSET_COVERAGE_AND_PROVIDER_SELECTION_FRAMEWORK.md"
    report = DOCS / "reports" / "PHASE4_9B_RESEARCH_ASSET_COVERAGE_PLANNER_AND_PROVIDER_SELECTION_FRAMEWORK.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in [architecture_doc, report, project_status, next_action, roadmap, master_index, retention_index]:
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "coverage-driven" in architecture_text.lower()
    assert "provider selection" in architecture_text.lower()
    assert "first production connector target" in architecture_text.lower()
    assert "worldview" in architecture_text.lower()
    assert "dataset.sports.nfl.schedule" in architecture_text

    assert "Phase 4.9B" in report_text
    assert "coverage planner" in report_text.lower()
    assert "provider selection framework" in report_text.lower()
    assert "first production connector target" in report_text.lower()
    assert "worldview" in report_text.lower()

    assert "Phase 4.9B - Research Asset Coverage Planner & Provider Selection Framework" in project_status_text
    assert "Phase 4.9C - First Production Connector (NFL Schedule)" in project_status_text
    assert "Phase 4.9F - NFL Weather Research Asset Population" in project_status_text
    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "docs/architecture/RESEARCH_ASSET_COVERAGE_AND_PROVIDER_SELECTION_FRAMEWORK.md" in project_status_text
    assert "docs/reports/PHASE4_9B_RESEARCH_ASSET_COVERAGE_PLANNER_AND_PROVIDER_SELECTION_FRAMEWORK.md" in project_status_text

    assert "Phase 4.9B builds the research asset coverage planner and provider selection framework." in roadmap_text
    assert "Phase 4.9C implements the first production connector for the NFL schedule research asset." in roadmap_text

    assert "docs/architecture/RESEARCH_ASSET_COVERAGE_AND_PROVIDER_SELECTION_FRAMEWORK.md" in master_index_text
    assert "docs/architecture/RESEARCH_ASSET_COVERAGE_AND_PROVIDER_SELECTION_FRAMEWORK.md" in retention_index_text
    assert "docs/reports/PHASE4_9B_RESEARCH_ASSET_COVERAGE_PLANNER_AND_PROVIDER_SELECTION_FRAMEWORK.md" in retention_index_text


def test_research_asset_coverage_planner_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_ASSET_COVERAGE_AND_PROVIDER_SELECTION_FRAMEWORK.md"
    report = DOCS / "reports" / "PHASE4_9B_RESEARCH_ASSET_COVERAGE_PLANNER_AND_PROVIDER_SELECTION_FRAMEWORK.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "from src." not in text.lower()
        assert "subprocess" not in text.lower()
        assert "coverage" in text.lower()
