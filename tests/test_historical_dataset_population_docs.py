from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_historical_dataset_population_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "HISTORICAL_DATASET_POPULATION_LAYER.md"
    report = DOCS / "reports" / "PHASE5_0_HISTORICAL_DATASET_POPULATION_LAYER.md"
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

    assert "Historical Dataset Population Layer" in architecture_text
    assert "dataset.sports.nfl.historical_dataset" in architecture_text
    assert "decision_cutoff = scheduled_kickoff_time - 5 minutes" in architecture_text
    assert "results remain label-only" in architecture_text.lower()
    assert "coverage_planner_snapshot_failed" in architecture_text
    assert "not_embedded" in architecture_text
    assert "cardinality" in architecture_text.lower()
    assert "lineage" in architecture_text.lower()

    assert "Phase 5.0 - Historical Dataset Population Layer" in report_text
    assert "Dataset Grain And Decision Cutoff" in report_text
    assert "Snapshot Selection And Cardinality Controls" in report_text
    assert "Persistence, Lineage, And Evidence Package" in report_text
    assert "Coverage Planner, Dashboard, And NFL P0 Integration" in report_text
    assert "Readiness For Phase 5.1" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text

    assert "Phase 5.0 historical dataset population code changes are complete and validated" in project_status_text
    assert "Phase 5.5 - Baseline Backtesting" in next_action_text
    assert "Phase 5.0 completed the historical dataset population layer" in roadmap_text
    assert "docs/architecture/HISTORICAL_DATASET_POPULATION_LAYER.md" in project_status_text
    assert "docs/reports/PHASE5_0_HISTORICAL_DATASET_POPULATION_LAYER.md" in project_status_text
    assert "docs/architecture/HISTORICAL_DATASET_POPULATION_LAYER.md" in master_index_text
    assert "docs/reports/PHASE5_0_HISTORICAL_DATASET_POPULATION_LAYER.md" in retention_index_text


def test_historical_dataset_population_docs_remain_documentation_only() -> None:
    for path in (
        DOCS / "architecture" / "HISTORICAL_DATASET_POPULATION_LAYER.md",
        DOCS / "reports" / "PHASE5_0_HISTORICAL_DATASET_POPULATION_LAYER.md",
    ):
        text = _read(path).lower()
        assert "subprocess" not in text
        assert "dataset.sports.nfl.historical_dataset" in text
