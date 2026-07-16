from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_historical_dataset_acquisition_framework_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md"
    report = DOCS / "reports" / "PHASE4_6_MINIMUM_CERTIFIED_HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    master_roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"
    dataset_registry = DOCS / "contracts" / "DATASET_REGISTRY.md"
    lineage_contract = DOCS / "contracts" / "DATA_LINEAGE_CONTRACT.md"

    for path in [
        architecture_doc,
        report,
        project_status,
        next_action,
        master_roadmap,
        master_index,
        retention_index,
        dataset_registry,
        lineage_contract,
    ]:
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(master_roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)
    dataset_registry_text = _read(dataset_registry)
    lineage_contract_text = _read(lineage_contract)

    assert "Historical Dataset Acquisition Framework" in architecture_text
    assert "acquisition lifecycle" in architecture_text.lower()
    assert "dataset versioning" in architecture_text.lower()
    assert "minimum nfl schema" in architecture_text.lower()
    assert "multi-provider" in architecture_text.lower()
    assert "quality assurance" in architecture_text.lower()
    assert "correction workflow" in architecture_text.lower()
    assert "dataset retirement" in architecture_text.lower()
    assert "dataset_version" in architecture_text
    assert "dataset_revision" in architecture_text
    assert "provider_sources" in architecture_text
    assert "provider_versions" in architecture_text
    assert "acquisition_timestamp" in architecture_text
    assert "certification_timestamp" in architecture_text
    assert "schema_version" in architecture_text
    assert "checksum" in architecture_text
    assert "lineage_id" in architecture_text
    assert "certification_status" in architecture_text
    assert "quality_score" in architecture_text
    assert "coverage_score" in architecture_text
    assert "Phase 4.6" in architecture_text
    assert "Phase 4.7" in architecture_text

    assert "Phase 4.6 Minimum Certified Historical Dataset Acquisition Framework" in report_text
    assert "Sources Evaluated" in report_text
    assert "Sources Selected for This Phase" in report_text
    assert "Framework Delivered" in report_text
    assert "Minimum NFL Dataset Contract" in report_text
    assert "Multi-Provider Architecture" in report_text
    assert "Shared Logic Reused" in report_text
    assert "Duplicate Logic Avoided" in report_text
    assert "Readiness for Phase 4.7" in report_text

    assert "Phase 4.7B - Historical Dataset Acquisition Runtime" in project_status_text
    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in project_status_text
    assert "docs/reports/PHASE4_6_MINIMUM_CERTIFIED_HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in project_status_text
    assert "certified and hardened nfl research pipeline" in next_action_text.lower()

    assert "Phase 4.6 defines the minimum certified historical dataset acquisition framework." in roadmap_text
    assert "Phase 4.7B builds the reusable historical dataset acquisition runtime with raw acquisition cache and integrity validation." in roadmap_text
    assert "Phase 4.7C completed the historical research asset certification runtime and gated dataset certification on asset-level evidence." in roadmap_text
    assert "Historical Dataset Acquisition Framework" in roadmap_text

    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in master_index_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in retention_index_text
    assert "docs/reports/PHASE4_6_MINIMUM_CERTIFIED_HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in retention_index_text

    assert "dataset_version" in dataset_registry_text
    assert "dataset_revision" in dataset_registry_text
    assert "provider_sources" in dataset_registry_text
    assert "provider_versions" in dataset_registry_text
    assert "acquisition_timestamp" in dataset_registry_text
    assert "certification_timestamp" in dataset_registry_text
    assert "schema_version" in dataset_registry_text
    assert "checksum" in dataset_registry_text
    assert "lineage_id" in dataset_registry_text
    assert "certification_status" in dataset_registry_text
    assert "quality_score" in dataset_registry_text
    assert "coverage_score" in dataset_registry_text

    assert "dataset_version" in lineage_contract_text
    assert "dataset_revision" in lineage_contract_text
    assert "acquisition_timestamp" in lineage_contract_text
    assert "certification_timestamp" in lineage_contract_text
    assert "certification_status" in lineage_contract_text
    assert "coverage_score" in lineage_contract_text
    assert "provider source -> acquisition job -> raw acquisition cache -> integrity validation -> normalization -> time and entity alignment certification -> research asset certification -> dataset certification -> certified dataset version" in lineage_contract_text.lower()


def test_historical_dataset_acquisition_framework_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md"
    report = DOCS / "reports" / "PHASE4_6_MINIMUM_CERTIFIED_HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "dataset" in text.lower()
