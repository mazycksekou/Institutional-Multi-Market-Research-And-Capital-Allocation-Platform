from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_nfl_odds_research_asset_population_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "NFL_ODDS_RESEARCH_ASSET.md"
    report = DOCS / "reports" / "PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md"
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

    assert "NFL Odds Research Asset" in architecture_text
    assert "dataset.nfl.odds_snapshots" in architecture_text
    assert "schedule and results join gate" in architecture_text.lower()
    assert "field-level provenance" in architecture_text.lower()
    assert "FEATURE_READY" in architecture_text
    assert "weather" in architecture_text.lower()

    assert "Phase 4.9E - NFL Odds Research Asset Population" in report_text
    assert "Source And Provider Role" in report_text
    assert "Field-Level Provenance" in report_text
    assert "Runtime Path" in report_text
    assert "Verified Minimum-Slice Behavior" in report_text
    assert "Query And Worldview Readiness" in report_text
    assert "Readiness For Phase 4.9F" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview Intelligence Review" in report_text

    assert "Phase 5.1B - Feature Snapshot Population (complete)" in project_status_text
    assert "Phase 5.2 - Reusable Mathematical Engines" in next_action_text
    assert "docs/architecture/NFL_ODDS_RESEARCH_ASSET.md" in project_status_text
    assert "docs/reports/PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md" in project_status_text
    assert "docs/architecture/NFL_ODDS_RESEARCH_ASSET.md" in master_index_text
    assert "docs/reports/PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md" in retention_index_text
    assert "weather" in next_action_text.lower()


def test_nfl_odds_research_asset_population_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "NFL_ODDS_RESEARCH_ASSET.md"
    report = DOCS / "reports" / "PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "odds" in text.lower()
