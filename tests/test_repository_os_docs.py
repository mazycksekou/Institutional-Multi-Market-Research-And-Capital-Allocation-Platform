from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_repository_os_documents_exist_and_reference_canonical_governance() -> None:
    repository_os = DOCS / "architecture" / "REPOSITORY_OS.md"
    validation_map = DOCS / "architecture" / "VALIDATION_OWNERSHIP_MAP.md"
    dependency_map = DOCS / "architecture" / "SUBSYSTEM_DEPENDENCY_MAP.md"
    impact_matrix = DOCS / "architecture" / "CHANGE_IMPACT_MATRIX.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    roadmap = DOCS / "MASTER_ROADMAP.md"
    status_policy = DOCS / "STATUS_UPDATE_POLICY.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in (
        repository_os,
        validation_map,
        dependency_map,
        impact_matrix,
        project_status,
        next_action,
        roadmap,
        status_policy,
        master_index,
        retention_index,
    ):
        assert path.exists(), path

    repository_os_text = _read(repository_os)
    validation_map_text = _read(validation_map)
    dependency_map_text = _read(dependency_map)
    impact_matrix_text = _read(impact_matrix)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(roadmap)
    status_policy_text = _read(status_policy)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "canonical execution policy" in repository_os_text.lower()
    assert "target 2-4 pages" in repository_os_text.lower()
    assert "index, not an encyclopedia" in repository_os_text.lower()
    assert "Execution Rules" in repository_os_text
    assert "Discovery Rules" in repository_os_text
    assert "Validation Policy" in repository_os_text
    assert "Repository Layer Order" in repository_os_text
    assert "Canonical Ownership Summary" in repository_os_text
    assert "AI Execution Policy" in repository_os_text
    assert "PROJECT_STATUS.md" in repository_os_text
    assert "NEXT_ACTION.md" in repository_os_text

    assert "Repository OS" in validation_map_text
    assert "Targeted validation is sufficient" in validation_map_text
    assert "Full repository gate is required" in validation_map_text

    assert "Governance layer" in dependency_map_text
    assert "Forbidden dependencies" in dependency_map_text
    assert "Reusable contracts" in dependency_map_text

    assert "Repository OS and execution policy" in impact_matrix_text
    assert "Full-gate requirement" in impact_matrix_text

    assert "docs/architecture/REPOSITORY_OS.md" in project_status_text
    assert "docs/architecture/REPOSITORY_OS.md" in next_action_text
    assert "docs/architecture/REPOSITORY_OS.md" in roadmap_text
    assert "docs/architecture/REPOSITORY_OS.md" in status_policy_text
    assert "docs/NEXT_ACTION.md" in repository_os_text
    assert "docs/PROJECT_STATUS.md" in repository_os_text
    assert "docs/MASTER_ROADMAP.md" in repository_os_text
    assert "docs/STATUS_UPDATE_POLICY.md" in repository_os_text
    assert "docs/MASTER_DOCUMENT_INDEX.md" in repository_os_text
    assert "docs/DOCUMENT_RETENTION_INDEX.md" in repository_os_text

    assert "Data Identity, Reconciliation and Lakehouse Foundation" in next_action_text
    assert "First Controlled NFL Vendor Ingest" in next_action_text
    assert "NFL Production Completion" in next_action_text
    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "Covariance and Time-Dependent Risk Capability Audit" in next_action_text
    assert "Parquet-based analytical storage" in next_action_text
    assert "Delta-compatible interfaces" in next_action_text
    assert "sole sequencing source" in next_action_text.lower()
    assert "canonical execution policy" in status_policy_text.lower()
    assert "sole sequencing source" in status_policy_text.lower()
    assert "canonical execution policy" in roadmap_text.lower()
    assert "sole sequencing source" in roadmap_text.lower()
    assert "canonical execution policy" in project_status_text.lower()
    assert "sole sequencing source" in project_status_text.lower()
    assert "docs/architecture/REPOSITORY_OS.md" in master_index_text
    assert "docs/architecture/VALIDATION_OWNERSHIP_MAP.md" in master_index_text
    assert "docs/architecture/SUBSYSTEM_DEPENDENCY_MAP.md" in master_index_text
    assert "docs/architecture/CHANGE_IMPACT_MATRIX.md" in master_index_text
    assert "docs/architecture/REPOSITORY_OS.md" in retention_index_text
    assert "docs/architecture/VALIDATION_OWNERSHIP_MAP.md" in retention_index_text
    assert "docs/architecture/SUBSYSTEM_DEPENDENCY_MAP.md" in retention_index_text
    assert "docs/architecture/CHANGE_IMPACT_MATRIX.md" in retention_index_text
