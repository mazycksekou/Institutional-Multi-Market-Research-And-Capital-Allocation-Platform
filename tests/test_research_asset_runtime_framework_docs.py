from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_research_asset_runtime_framework_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_ASSET_RUNTIME_FRAMEWORK.md"
    contract_doc = DOCS / "contracts" / "RESEARCH_ASSET_CONTRACT.md"
    report = DOCS / "reports" / "PHASE4_5D_RESEARCH_ASSET_RUNTIME_FRAMEWORK.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    master_roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    contract_index = DOCS / "contracts" / "CONTRACT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in [
        architecture_doc,
        contract_doc,
        report,
        project_status,
        next_action,
        master_roadmap,
        master_index,
        contract_index,
        retention_index,
    ]:
        assert path.exists(), f"missing document: {path}"

    architecture_matches = sorted(path.resolve() for path in DOCS.rglob("RESEARCH_ASSET_RUNTIME_FRAMEWORK.md"))
    contract_matches = sorted(path.resolve() for path in DOCS.rglob("RESEARCH_ASSET_CONTRACT.md"))
    report_matches = sorted(path.resolve() for path in DOCS.rglob("PHASE4_5D_RESEARCH_ASSET_RUNTIME_FRAMEWORK.md"))
    assert architecture_matches == [architecture_doc.resolve()]
    assert contract_matches == [contract_doc.resolve()]
    assert report_matches == [report.resolve()]

    architecture_text = _read(architecture_doc)
    contract_text = _read(contract_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(master_roadmap)
    master_index_text = _read(master_index)
    contract_index_text = _read(contract_index)
    retention_index_text = _read(retention_index)

    assert "Research Asset Runtime Framework" in architecture_text
    assert "datasets" in architecture_text.lower()
    assert "features" in architecture_text.lower()
    assert "mathematical engines" in architecture_text.lower()
    assert "signals" in architecture_text.lower()
    assert "targets" in architecture_text.lower()
    assert "confidence measures" in architecture_text.lower()
    assert "decision rows" in architecture_text.lower()
    assert "backtests" in architecture_text.lower()
    assert "experiments" in architecture_text.lower()
    assert "evidence packages" in architecture_text.lower()
    assert "Research Asset ID" in architecture_text
    assert "category.family.scope.name" in architecture_text
    assert "Asset Category" in architecture_text
    assert "Owner" in architecture_text
    assert "Dependencies" in architecture_text
    assert "Consumes" in architecture_text
    assert "Produces" in architecture_text
    assert "Lifecycle" in architecture_text
    assert "Versioning" in architecture_text
    assert "Validation Owner" in architecture_text
    assert "Storage Owner" in architecture_text
    assert "Profile Owner" in architecture_text
    assert "Runtime Owner" in architecture_text
    assert "Evidence Requirements" in architecture_text
    assert "Point-in-Time Rules" in architecture_text
    assert "Lineage Requirements" in architecture_text
    assert "Supported Markets" in architecture_text
    assert "Priority" in architecture_text
    assert "Discovered -> Source Identified -> Connector Mapped" in architecture_text
    assert "Raw Acquired" in architecture_text
    assert "Integrity Verified" in architecture_text
    assert "Normalized" in architecture_text
    assert "Research Asset Certified" in architecture_text
    assert "Dataset Certified" in architecture_text
    assert "Feature Ready" in architecture_text
    assert "Math Ready" in architecture_text
    assert "Signal Ready" in architecture_text
    assert "Backtest Ready" in architecture_text
    assert "Production Ready" in architecture_text
    assert "minimum-schema-first" in architecture_text.lower()
    assert "research asset registry" in architecture_text.lower()

    assert "Research Asset Contract" in contract_text
    assert "Research Asset ID" in contract_text
    assert "Asset Category" in contract_text
    assert "Evidence Requirements" in contract_text
    assert "Point-in-Time Rules" in contract_text
    assert "Lineage Requirements" in contract_text
    assert "Supported Markets" in contract_text
    assert "Priority" in contract_text
    assert "Discovered -> Source Identified -> Connector Ready" in contract_text
    assert "Raw Acquired" in contract_text
    assert "Integrity Verified" in contract_text
    assert "Normalized" in contract_text
    assert "Research Asset Certified" in contract_text
    assert "Dataset Certified" in contract_text
    assert "Feature Ready" in contract_text
    assert "Math Ready" in contract_text
    assert "Signal Ready" in contract_text
    assert "Backtest Ready" in contract_text
    assert "Production Ready" in contract_text
    assert "dataset.nfl.games" in contract_text
    assert "connector.theoddsapi" in contract_text
    assert "decision row" in contract_text.lower()

    assert "Phase 4.5D - Research Asset Runtime Framework" in report_text
    assert "Existing Research Asset Abstractions Discovered" in report_text
    assert "Existing Abstractions Reused" in report_text
    assert "Research Asset Runtime Framework Created Or Extended" in report_text
    assert "Research Asset Categories Documented" in report_text
    assert "Runtime Dependency Framework Documented" in report_text
    assert "Research Asset ID Standard Documented" in report_text
    assert "Lifecycle Framework Documented" in report_text
    assert "Duplicate Systems Avoided" in report_text
    assert "Engineering Improvements Implemented" in report_text
    assert "Engineering Improvements Deferred" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview Intelligence Review" in report_text
    assert "MASTER_RESEARCH_ENGINE_SPECIFICATION" in report_text
    assert "Readiness for Phase 4.7" in report_text

    assert "Phase 4.5E - Canonical Engineering Specification Rename & Research Asset Runtime Framework" in project_status_text
    assert "Phase 5.0 - Historical Dataset Population Layer" in next_action_text
    assert "docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in project_status_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in project_status_text
    assert "docs/contracts/RESEARCH_ASSET_CONTRACT.md" in project_status_text
    assert "docs/reports/PHASE4_5D_RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in project_status_text
    assert "minimum certified schema first" in next_action_text.lower()
    assert "do not backtest" in next_action_text.lower()
    assert "do not add provider-specific runtime ownership" in next_action_text.lower()

    assert "Phase 4.5D established the research asset runtime framework." in roadmap_text
    assert "Phase 4.5E renamed the master research engine specification and the research asset runtime framework" in roadmap_text
    assert "Phase 4.6 defines the minimum certified historical dataset acquisition framework." in roadmap_text
    assert "Phase 4.7B builds the reusable historical dataset acquisition runtime with raw acquisition cache and integrity validation." in roadmap_text
    assert "Phase 4.7C completed the historical research asset certification runtime and gated dataset certification on asset-level evidence." in roadmap_text
    assert "Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification." in roadmap_text
    assert "Phase 4.9A populates the NFL schedule research asset." in roadmap_text
    assert "Phase 4.9B builds the research asset coverage planner and provider selection framework." in roadmap_text
    assert "Phase 4.9C implements the first production connector for the NFL schedule research asset." in roadmap_text
    assert "Phase 5.0 materializes the historical dataset population layer." in roadmap_text
    assert "Phase 5.1 populates reusable features from certified assets and certified events." in roadmap_text
    assert "minimum certified schema" in roadmap_text.lower()
    assert "research asset runtime framework" in roadmap_text.lower()

    assert "docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in master_index_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in master_index_text
    assert "docs/contracts/RESEARCH_ASSET_CONTRACT.md" in master_index_text
    assert "Research asset contract" in contract_index_text
    assert "docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in retention_index_text
    assert "docs/contracts/RESEARCH_ASSET_CONTRACT.md" in retention_index_text
    assert "docs/reports/PHASE4_5D_RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in retention_index_text


def test_research_asset_runtime_framework_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "RESEARCH_ASSET_RUNTIME_FRAMEWORK.md"
    contract_doc = DOCS / "contracts" / "RESEARCH_ASSET_CONTRACT.md"
    report = DOCS / "reports" / "PHASE4_5D_RESEARCH_ASSET_RUNTIME_FRAMEWORK.md"

    for text in (_read(architecture_doc), _read(contract_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "research asset" in text.lower()
