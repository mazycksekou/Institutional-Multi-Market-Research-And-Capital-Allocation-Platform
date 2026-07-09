from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_research_asset_source_discovery_and_connector_mapping_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md"
    report = DOCS / "reports" / "PHASE4_7A_RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    master_roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in [architecture_doc, report, project_status, next_action, master_roadmap, master_index, retention_index]:
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(master_roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "Research Asset Source Discovery And Connector Mapping" in architecture_text
    assert "src.data.data_source_registry" in architecture_text
    assert "src.providers" in architecture_text
    assert "src.connectors" in architecture_text
    assert "Minimum NFL Source Map" in architecture_text
    assert "dataset.nfl.games" in architecture_text
    assert "dataset.nfl.odds_snapshots" in architecture_text
    assert "dataset.nfl.weather_snapshots" in architecture_text
    assert "dataset.nfl.team_stats_snapshots" in architecture_text
    assert "dataset.nfl.rest_travel" in architecture_text
    assert "connector mapping" in architecture_text.lower()
    assert "MLB" in architecture_text
    assert "prediction markets" in architecture_text.lower()
    assert "options / 0dte" in architecture_text.lower()

    assert "Phase 4.7A Research Asset Source Discovery And Connector Mapping" in report_text
    assert "Sources Evaluated" in report_text
    assert "Sources Selected For The Minimum NFL Schema" in report_text
    assert "Optional Enrichment Sources" in report_text
    assert "Connector Mapping Summary" in report_text
    assert "Readiness For Phase 4.7B - Historical Dataset Acquisition Runtime" in report_text

    assert "Phase 4.7B - Historical Dataset Acquisition Runtime" in project_status_text
    assert "Phase 4.9D - NFL Results Research Asset Population" in next_action_text
    assert "docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in project_status_text
    assert "docs/reports/PHASE4_7A_RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in project_status_text
    assert "Phase 4.7A" in roadmap_text
    assert "Phase 4.7B builds the reusable historical dataset acquisition runtime" in roadmap_text
    assert "docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in master_index_text
    assert "docs/reports/PHASE4_7A_RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in master_index_text
    assert "docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in retention_index_text
    assert "docs/reports/PHASE4_7A_RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in retention_index_text
