from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_nfl_team_statistics_research_asset_population_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "NFL_TEAM_STATISTICS_RESEARCH_ASSET.md"
    report = DOCS / "reports" / "PHASE4_9H_NFL_TEAM_STATISTICS_RESEARCH_ASSET_POPULATION.md"
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

    assert "NFL Team Statistics Research Asset" in architecture_text
    assert "dataset.nfl.team_stats_snapshots" in architecture_text
    assert "same-event live statistics" in architecture_text.lower()
    assert "field-level provenance" in architecture_text.lower()
    assert "FEATURE_READY" in architecture_text
    assert "row-level alignment evidence" in architecture_text.lower()

    assert "Phase 4.9H - NFL Team Statistics Research Asset Population" in report_text
    assert "Point-In-Time And Leakage Controls" in report_text
    assert "Runtime Path" in report_text
    assert "Verified Minimum-Slice Behavior" in report_text
    assert "Query And Worldview Readiness" in report_text
    assert "Readiness For Phase 5.0" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text

    assert "Phase 4.9H - NFL Team Statistics Research Asset Population (complete)" in project_status_text
    assert "Phase 5.0 - Historical Dataset Population Layer" in next_action_text
    assert "Phase 5.0 will materialize the historical dataset population layer" in roadmap_text
    assert "docs/architecture/NFL_TEAM_STATISTICS_RESEARCH_ASSET.md" in project_status_text
    assert "docs/reports/PHASE4_9H_NFL_TEAM_STATISTICS_RESEARCH_ASSET_POPULATION.md" in project_status_text
    assert "docs/architecture/NFL_TEAM_STATISTICS_RESEARCH_ASSET.md" in master_index_text
    assert "docs/reports/PHASE4_9H_NFL_TEAM_STATISTICS_RESEARCH_ASSET_POPULATION.md" in retention_index_text


def test_nfl_team_statistics_research_asset_population_docs_remain_documentation_only() -> None:
    for path in (
        DOCS / "architecture" / "NFL_TEAM_STATISTICS_RESEARCH_ASSET.md",
        DOCS / "reports" / "PHASE4_9H_NFL_TEAM_STATISTICS_RESEARCH_ASSET_POPULATION.md",
    ):
        text = _read(path).lower()
        assert "subprocess" not in text
        assert "dataset.nfl.team_stats_snapshots" in text
