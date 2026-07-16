from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_nfl_results_research_asset_docs_and_governance_are_current() -> None:
    architecture_doc = DOCS / "architecture" / "NFL_RESULTS_RESEARCH_ASSET.md"
    report = DOCS / "reports" / "PHASE4_9D_NFL_RESULTS_RESEARCH_ASSET_POPULATION.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in (
        architecture_doc,
        report,
        project_status,
        next_action,
        roadmap,
        master_index,
        retention_index,
    ):
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "dataset.sports.nfl.results" in architecture_text
    assert "schedule join gate" in architecture_text.lower()
    assert "field-level provenance" in architecture_text.lower()
    assert "raw acquisition cache" in architecture_text.lower()
    assert "worldview" in architecture_text.lower()
    assert "multi-event" in architecture_text.lower()

    assert "Phase 4.9D" in report_text
    assert "dataset.sports.nfl.results" in report_text
    assert "negative gate proof" in report_text.lower()
    assert "Readiness For Phase 4.9E" in report_text

    assert "Phase 4.9F - NFL Weather Research Asset Population" in project_status_text
    assert "docs/architecture/NFL_ODDS_RESEARCH_ASSET.md" in project_status_text
    assert "docs/reports/PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md" in project_status_text
    assert "docs/architecture/NFL_RESULTS_RESEARCH_ASSET.md" in project_status_text
    assert "docs/reports/PHASE4_9D_NFL_RESULTS_RESEARCH_ASSET_POPULATION.md" in project_status_text
    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "Phase 4.9E completes the NFL odds research asset population" in roadmap_text
    assert "Phase 5.0 completed the historical dataset population layer" in roadmap_text

    assert "docs/architecture/NFL_RESULTS_RESEARCH_ASSET.md" in master_index_text
    assert "docs/architecture/NFL_RESULTS_RESEARCH_ASSET.md" in retention_index_text
    assert "docs/reports/PHASE4_9D_NFL_RESULTS_RESEARCH_ASSET_POPULATION.md" in retention_index_text


def test_nfl_results_research_asset_docs_remain_documentation_only() -> None:
    for path in (
        DOCS / "architecture" / "NFL_RESULTS_RESEARCH_ASSET.md",
        DOCS / "reports" / "PHASE4_9D_NFL_RESULTS_RESEARCH_ASSET_POPULATION.md",
    ):
        text = _read(path).lower()
        assert "subprocess" not in text
        assert "dataset.sports.nfl.results" in text
