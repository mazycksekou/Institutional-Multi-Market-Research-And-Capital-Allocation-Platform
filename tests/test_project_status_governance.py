from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_project_status_governance_files_exist_and_are_canonical() -> None:
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    status_policy = DOCS / "STATUS_UPDATE_POLICY.md"
    discovery_report = DOCS / "reports" / "PROJECT_STATUS_GOVERNANCE_DISCOVERY.md"
    entrypoint_audit = DOCS / "reports" / "PROJECT_ENTRYPOINT_AUDIT.md"
    odds_architecture = DOCS / "architecture" / "NFL_ODDS_RESEARCH_ASSET.md"
    master_roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    assert project_status.exists()
    assert next_action.exists()
    assert status_policy.exists()
    assert discovery_report.exists()
    assert entrypoint_audit.exists()
    assert odds_architecture.exists()
    assert master_roadmap.exists()
    assert master_index.exists()
    assert retention_index.exists()

    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    status_policy_text = _read(status_policy)
    entrypoint_audit_text = _read(entrypoint_audit)
    roadmap_text = _read(master_roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "required starting document" in project_status_text.lower()
    assert "repository homepage" in project_status_text.lower()
    assert "current branch: `main`" in project_status_text
    assert "active phase: `Covariance and Time-Dependent Risk Capability Audit`" in project_status_text
    assert "next phase: `Implement only covariance and risk capabilities confirmed missing by that audit`" in project_status_text
    assert (
        "governed handoff after the active phase: "
        "`Implement only covariance and risk capabilities confirmed missing by that audit`"
        in project_status_text
    )
    assert (
        "`Covariance and Time-Dependent Risk Capability Audit`"
        in project_status_text
    )
    assert "validated canonical branch: `main`" in project_status_text
    assert "sports:nfl" in project_status_text
    assert "Phase 4.9A - NFL Schedule Research Asset Population" in project_status_text
    assert "Phase 4.9C - First Production Connector (NFL Schedule)" in project_status_text
    assert "Phase 4.9D - NFL Results Research Asset Population" in project_status_text
    assert "Phase 4.9E - NFL Odds Research Asset Population" in project_status_text
    assert "Phase 4.7B - Historical Dataset Acquisition Runtime" in project_status_text
    assert "Phase 4.7C - Historical Research Asset Certification Runtime" in project_status_text
    assert "Phase 4.8 - Research Asset Lifecycle Runtime & Time & Entity Alignment Certification" in project_status_text
    assert "Phase 4.5E - Canonical Engineering Specification Rename & Research Asset Runtime Framework" in project_status_text
    assert "Phase 4.5C - Universal Math Engine Contracts" in project_status_text
    assert "Phase 4.3.6" in project_status_text
    assert "Phase 4.3.7" in project_status_text
    assert "First Controlled NFL Vendor Ingest" in project_status_text
    assert "Portable External Research-Data Storage" in project_status_text
    assert "Portable External Research-Data Storage (complete)" in project_status_text
    assert "Data Identity, Reconciliation and Lakehouse Foundation (complete)" in project_status_text
    assert "NFL Production Completion" in project_status_text
    assert "Universal Market Framework (complete)" in project_status_text
    assert "Data Identity, Reconciliation and Lakehouse Foundation" in project_status_text
    assert "First Controlled NFL Vendor Ingest" in project_status_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in project_status_text
    assert "exact 1,000-row replay" in project_status_text
    assert "full 5,075-row ingestion" in project_status_text
    assert "exact full replay is green" in project_status_text
    assert "dataset-certified" in project_status_text
    assert "repository-owned retrieval is verified without reopening `NFL_Basic.csv`" in project_status_text
    assert "master research engine specification" in project_status_text.lower()
    assert "latest validation status" in project_status_text.lower()
    assert "latest full gate result" in project_status_text.lower()
    assert "next recommended codex task" in project_status_text.lower()
    assert "docs/MASTER_ROADMAP.md" in project_status_text
    assert "docs/MASTER_DOCUMENT_INDEX.md" in project_status_text
    assert "docs/DOCUMENT_RETENTION_INDEX.md" in project_status_text
    assert "docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md" in project_status_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in project_status_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_RUNTIME.md" in project_status_text
    assert "docs/architecture/HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md" in project_status_text
    assert "docs/architecture/NFL_SCHEDULE_RESEARCH_ASSET.md" in project_status_text
    assert "docs/architecture/NFL_ODDS_RESEARCH_ASSET.md" in project_status_text
    assert "docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in project_status_text
    assert "docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md" in project_status_text
    assert "docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in project_status_text
    assert "docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in project_status_text
    assert "docs/architecture/DECISION_ROW_POPULATION_LAYER.md" in project_status_text
    assert "docs/architecture/DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in project_status_text
    assert "docs/contracts/RESEARCH_ASSET_CONTRACT.md" in project_status_text
    assert "docs/reports/PHASE4_5A_MASTER_RESEARCH_ENGINE_SPECIFICATION.md" in project_status_text
    assert "docs/reports/PHASE4_5B_UNIVERSAL_FEATURE_REGISTRY.md" in project_status_text
    assert "docs/reports/PHASE4_5C_UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in project_status_text
    assert "docs/reports/PHASE4_5D_RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in project_status_text
    assert "docs/reports/PHASE4_7A_RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in project_status_text
    assert "docs/reports/PHASE4_7B_HISTORICAL_DATASET_ACQUISITION_RUNTIME.md" in project_status_text
    assert "docs/reports/PHASE4_7C_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md" in project_status_text
    assert "docs/reports/PHASE4_9A_NFL_SCHEDULE_RESEARCH_ASSET_POPULATION.md" in project_status_text
    assert "docs/reports/PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md" in project_status_text
    assert "docs/reports/PHASE5_4_DECISION_ROW_GENERATION.md" in project_status_text
    assert "docs/reports/PHASE5_5_BASELINE_BACKTESTING.md" in project_status_text
    assert "docs/reports/PHASE5_9_DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in project_status_text

    assert "Data Identity, Reconciliation and Lakehouse Foundation" in next_action_text
    assert "First Controlled NFL Vendor Ingest" in next_action_text
    assert "Portable External Research-Data Storage" in next_action_text
    assert "NFL Production Completion" in next_action_text
    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in next_action_text
    assert "Research Intelligence" in next_action_text
    assert "covariance and time-dependent risk capability audit" in next_action_text.lower()
    assert "certified repository-owned oddswarehouse historical dataset" in next_action_text.lower()
    assert "exact 1,000-row replay is green" in next_action_text.lower()
    assert "exact full replay is green" in next_action_text.lower()
    assert "dataset certification is complete" in next_action_text.lower()
    assert "repository-owned retrieval is verified" in next_action_text.lower()
    assert "do not implement covariance or the risk engine during the audit." in next_action_text.lower()
    assert "do not create a parallel ingestion, storage, certification, lifecycle, identity, reconciliation, or retrieval framework." in next_action_text.lower()
    assert "validation commands" in next_action_text.lower()

    assert "Every new session begins with `docs/PROJECT_STATUS.md`." in status_policy_text
    assert "single required repository entrypoint" in status_policy_text
    assert "docs/architecture/REPOSITORY_OS.md" in status_policy_text
    assert "sole sequencing source" in status_policy_text.lower()
    assert "Every Codex task must update the canonical project status." in status_policy_text
    assert "Every Codex task must update the canonical next-action file." in status_policy_text
    assert "MASTER_DOCUMENT_INDEX.md" in status_policy_text
    assert "DOCUMENT_RETENTION_INDEX.md" in status_policy_text

    assert "entrypoint verification" in entrypoint_audit_text.lower()
    assert "supporting document ownership" in entrypoint_audit_text.lower()
    assert "duplicate ownership analysis" in entrypoint_audit_text.lower()
    assert "recommendations" in entrypoint_audit_text.lower()

    assert "Phase 4.5A defined the master research engine specification." in roadmap_text
    assert "Phase 4.5B built the universal feature registry." in roadmap_text
    assert "Phase 4.5C defines the universal math engine contracts." in roadmap_text
    assert "Phase 4.5D established the research asset runtime framework." in roadmap_text
    assert "Phase 4.5E renamed the master research engine specification and the research asset runtime framework to reflect the broader runtime ownership model." in roadmap_text
    assert "Phase 4.6 defines the minimum certified historical dataset acquisition framework." in roadmap_text
    assert "Phase 4.7A discovers and maps research asset sources and connector families" in roadmap_text
    assert "Phase 4.7B builds the reusable historical dataset acquisition runtime with raw acquisition cache and integrity validation." in roadmap_text
    assert "Phase 4.7C completed the historical research asset certification runtime and gated dataset certification on asset-level evidence." in roadmap_text
    assert "Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification." in roadmap_text
    assert "Phase 4.9A populates the NFL schedule research asset." in roadmap_text
    assert "Phase 4.9B builds the research asset coverage planner and provider selection framework." in roadmap_text
    assert "Phase 4.9C implements the first production connector for the NFL schedule research asset." in roadmap_text
    assert "Phase 4.9E completes the NFL odds research asset population" in roadmap_text
    assert "Phase 4.9J populates the NFL betting splits research asset." in roadmap_text
    assert "Phase 5.0 completed the historical dataset population layer" in roadmap_text
    assert "Phase 5.1B completed the reusable feature snapshot population layer from certified historical dataset rows." in roadmap_text
    assert "Phase 5.2 completed reusable mathematical engines." in roadmap_text
    assert "Phase 5.3 completed reusable signals." in roadmap_text
    assert "Phase 5.4 completed the decision-row generation layer from the certified signal layer." in roadmap_text
    assert "Phase 5.5 completed baseline backtesting from frozen, certified inputs." in roadmap_text
    assert "Phase 5.6 completed pipeline validation and hardening on the production research engine path." in roadmap_text
    assert "Phase 5.7 completed deterministic Research Intelligence on top of the certified NFL pipeline." in roadmap_text
    assert "NFL Production Completion" in roadmap_text
    assert "Data Identity, Reconciliation and Lakehouse Foundation" in roadmap_text
    assert "First Controlled NFL Vendor Ingest" in roadmap_text
    assert "Portable External Research-Data Storage" in roadmap_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in roadmap_text
    assert "Implement only covariance and risk capabilities confirmed missing by that audit" in roadmap_text
    assert "additional sports" in roadmap_text
    assert "universal risk and capital allocation" in roadmap_text
    assert "docs/PROJECT_STATUS.md" in roadmap_text
    assert "docs/NEXT_ACTION.md" in roadmap_text
    assert "docs/architecture/REPOSITORY_OS.md" in roadmap_text
    assert "docs/STATUS_UPDATE_POLICY.md" in roadmap_text
    assert "docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md" in roadmap_text
    assert "docs/architecture/NFL_ODDS_RESEARCH_ASSET.md" in roadmap_text
    assert "docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in roadmap_text
    assert "docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md" in roadmap_text
    assert "docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in roadmap_text
    assert "docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in roadmap_text
    assert "docs/contracts/RESEARCH_ASSET_CONTRACT.md" in roadmap_text
    assert "MASTER_RESEARCH_ENGINE_SPECIFICATION.md" in roadmap_text
    assert "docs/architecture/HISTORICAL_RESEARCH_DATABASE.md" in roadmap_text

    assert "docs/PROJECT_STATUS.md" in master_index_text
    assert "docs/NEXT_ACTION.md" in master_index_text
    assert "docs/STATUS_UPDATE_POLICY.md" in master_index_text
    assert "docs/architecture/REPOSITORY_OS.md" in master_index_text
    assert "docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md" in master_index_text
    assert "docs/architecture/NFL_SCHEDULE_RESEARCH_ASSET.md" in master_index_text
    assert "docs/architecture/NFL_ODDS_RESEARCH_ASSET.md" in master_index_text
    assert "docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in master_index_text
    assert "docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md" in master_index_text
    assert "docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in master_index_text
    assert "docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in master_index_text
    assert "docs/architecture/DECISION_ROW_POPULATION_LAYER.md" in master_index_text
    assert "docs/architecture/DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in master_index_text
    assert "docs/architecture/HISTORICAL_RESEARCH_DATABASE.md" in master_index_text
    assert "docs/contracts/RESEARCH_ASSET_CONTRACT.md" in master_index_text

    assert "docs/reports/PROJECT_ENTRYPOINT_AUDIT.md" in retention_index_text
    assert "docs/reports/PROJECT_STATUS_GOVERNANCE_DISCOVERY.md" in retention_index_text
    assert "docs/architecture/REPOSITORY_OS.md" in retention_index_text
    assert "docs/reports/PHASE4_7A_RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md" in retention_index_text
    assert "docs/reports/PHASE4_5A_MASTER_RESEARCH_ENGINE_SPECIFICATION.md" in retention_index_text
    assert "docs/reports/PHASE4_5B_UNIVERSAL_FEATURE_REGISTRY.md" in retention_index_text
    assert "docs/reports/PHASE4_5C_UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in retention_index_text
    assert "docs/reports/PHASE4_5D_RESEARCH_ASSET_RUNTIME_FRAMEWORK.md" in retention_index_text
    assert "docs/reports/PHASE4_4_EVENT_CENTRIC_HISTORICAL_ACQUISITION.md" in retention_index_text
    assert "docs/architecture/NFL_SCHEDULE_RESEARCH_ASSET.md" in retention_index_text
    assert "docs/architecture/NFL_ODDS_RESEARCH_ASSET.md" in retention_index_text
    assert "docs/reports/PHASE4_9A_NFL_SCHEDULE_RESEARCH_ASSET_POPULATION.md" in retention_index_text
    assert "docs/reports/PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md" in retention_index_text
    assert "docs/reports/PHASE5_4_DECISION_ROW_GENERATION.md" in retention_index_text
    assert "docs/reports/PHASE5_5_BASELINE_BACKTESTING.md" in retention_index_text
    assert "docs/architecture/DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in retention_index_text
    assert "docs/reports/PHASE5_9_DATA_IDENTITY_RECONCILIATION_AND_LAKEHOUSE_FOUNDATION.md" in retention_index_text


def test_project_status_governance_has_no_duplicate_status_files() -> None:
    canonical_files = {
        "PROJECT_STATUS.md": DOCS / "PROJECT_STATUS.md",
        "NEXT_ACTION.md": DOCS / "NEXT_ACTION.md",
        "STATUS_UPDATE_POLICY.md": DOCS / "STATUS_UPDATE_POLICY.md",
    }

    for filename, canonical_path in canonical_files.items():
        matches = sorted(
            path.resolve()
            for path in DOCS.rglob(filename)
            if path.is_file()
        )
        assert matches == [canonical_path.resolve()], f"unexpected duplicates for {filename}: {matches}"
