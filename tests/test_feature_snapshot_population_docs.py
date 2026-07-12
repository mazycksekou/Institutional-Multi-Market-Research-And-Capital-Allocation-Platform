from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_feature_snapshot_population_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "FEATURE_SNAPSHOT_POPULATION_LAYER.md"
    report = DOCS / "reports" / "PHASE5_1B_FEATURE_SNAPSHOT_POPULATION.md"
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

    assert "Feature Snapshot Population Layer" in architecture_text
    assert "dataset.sports.nfl.historical_dataset" in architecture_text
    assert "decision_cutoff_time = scheduled_kickoff_time - 5 minutes" in architecture_text
    assert "dataset_row_id" in architecture_text
    assert "decision_context_id" in architecture_text
    assert "feature_id" in architecture_text
    assert "transformation_version" in architecture_text
    assert "38 registered features across 3 dataset contexts" in architecture_text
    assert "114 persisted feature rows" in architecture_text
    assert "3 dataset contexts" in architecture_text
    assert "lineage" in architecture_text.lower()
    assert "evidence package" in architecture_text.lower()

    assert "Phase 5.1B - Feature Snapshot Population" in report_text
    assert "Dataset Grain And Fixture Context" in report_text
    assert "Population Behavior" in report_text
    assert "Canonical Owners Reused" in report_text
    assert "Validation" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text

    assert "Phase 5.3 - Reusable Signals" in project_status_text
    assert "Phase 5.3 - Reusable Signals" in project_status_text
    assert "Phase 5.5 - Baseline Backtesting" in next_action_text
    assert "Phase 5.1B completed the reusable feature snapshot population layer" in roadmap_text
    assert "Phase 5.2 completed reusable mathematical engines." in roadmap_text

    assert "docs/architecture/FEATURE_SNAPSHOT_POPULATION_LAYER.md" in master_index_text
    assert "docs/reports/PHASE5_1B_FEATURE_SNAPSHOT_POPULATION.md" in master_index_text
    assert "docs/architecture/FEATURE_SNAPSHOT_POPULATION_LAYER.md" in retention_index_text
    assert "docs/reports/PHASE5_1B_FEATURE_SNAPSHOT_POPULATION.md" in retention_index_text


def test_feature_snapshot_population_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "FEATURE_SNAPSHOT_POPULATION_LAYER.md"
    report = DOCS / "reports" / "PHASE5_1B_FEATURE_SNAPSHOT_POPULATION.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "feature" in text.lower()
