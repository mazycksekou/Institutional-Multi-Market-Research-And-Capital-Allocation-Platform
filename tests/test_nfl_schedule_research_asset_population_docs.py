from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_nfl_schedule_research_asset_population_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "NFL_SCHEDULE_RESEARCH_ASSET.md"
    report = DOCS / "reports" / "PHASE4_9A_NFL_SCHEDULE_RESEARCH_ASSET_POPULATION.md"
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

    assert "dataset.sports.nfl.schedule" in architecture_text
    assert "raw acquisition cache" in architecture_text.lower()
    assert "time and entity alignment" in architecture_text.lower()
    assert "Research Query Engine" in architecture_text
    assert "Worldview" in architecture_text
    assert "feature_ready" in architecture_text.lower()

    assert "Phase 4.9A" in report_text
    assert "deterministic local fixture" in report_text.lower()
    assert "raw acquisition cache" in report_text.lower()
    assert "normalization" in report_text.lower()
    assert "certification" in report_text.lower()
    assert "Readiness for Phase 4.9B - Research Asset Coverage Planner & Provider Selection Framework" in report_text

    assert "Phase 4.9A - NFL Schedule Research Asset Population" in project_status_text
    assert "Phase 4.9B - Research Asset Coverage Planner & Provider Selection Framework" in project_status_text
    assert "Phase 4.9C - First Production Connector (NFL Schedule)" in project_status_text
    assert "Phase 4.9F - NFL Weather Research Asset Population" in project_status_text
    assert "docs/architecture/NFL_ODDS_RESEARCH_ASSET.md" in project_status_text
    assert "docs/reports/PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md" in project_status_text
    assert "docs/architecture/NFL_SCHEDULE_RESEARCH_ASSET.md" in project_status_text
    assert "docs/reports/PHASE4_9A_NFL_SCHEDULE_RESEARCH_ASSET_POPULATION.md" in project_status_text

    assert "Phase 4.9H - NFL Team Statistics Research Asset Population" in next_action_text
    assert "canonical connector" in next_action_text.lower()
    assert "canonical open-provider acquisition path" in next_action_text.lower()

    assert "Phase 4.9A populates the NFL schedule research asset." in roadmap_text
    assert "Phase 4.9B builds the research asset coverage planner and provider selection framework." in roadmap_text
    assert "Phase 4.9C implements the first production connector for the NFL schedule research asset." in roadmap_text
    assert "Phase 4.9J populates the NFL betting splits research asset." in roadmap_text

    assert "docs/architecture/NFL_SCHEDULE_RESEARCH_ASSET.md" in master_index_text
    assert "docs/reports/PHASE4_9A_NFL_SCHEDULE_RESEARCH_ASSET_POPULATION.md" in master_index_text
    assert "docs/architecture/NFL_SCHEDULE_RESEARCH_ASSET.md" in retention_index_text
    assert "docs/reports/PHASE4_9A_NFL_SCHEDULE_RESEARCH_ASSET_POPULATION.md" in retention_index_text


def test_nfl_schedule_research_asset_population_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "NFL_SCHEDULE_RESEARCH_ASSET.md"
    report = DOCS / "reports" / "PHASE4_9A_NFL_SCHEDULE_RESEARCH_ASSET_POPULATION.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "schedule" in text.lower()
