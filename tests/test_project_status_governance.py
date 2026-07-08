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
    master_roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    assert project_status.exists()
    assert next_action.exists()
    assert status_policy.exists()
    assert discovery_report.exists()
    assert entrypoint_audit.exists()
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
    assert "feature/nfl-backtesting" in project_status_text
    assert "sports:nfl" in project_status_text
    assert "Phase 4.5A - Master Market Input Specification" in project_status_text
    assert "Phase 4.3.6" in project_status_text
    assert "Phase 4.3.7" in project_status_text
    assert "master market input specification" in project_status_text.lower()
    assert "latest validation status" in project_status_text.lower()
    assert "latest full gate result" in project_status_text.lower()
    assert "next recommended codex task" in project_status_text.lower()
    assert "docs/MASTER_ROADMAP.md" in project_status_text
    assert "docs/MASTER_DOCUMENT_INDEX.md" in project_status_text
    assert "docs/DOCUMENT_RETENTION_INDEX.md" in project_status_text
    assert "docs/architecture/MASTER_MARKET_INPUT_SPECIFICATION.md" in project_status_text
    assert "docs/reports/PHASE4_5A_MASTER_MARKET_INPUT_SPECIFICATION.md" in project_status_text

    assert "Phase 4.5B - Universal Feature Registry" in next_action_text
    assert "turn the master market input specification into the universal feature registry" in next_action_text.lower()
    assert "Do not ingest paid or live data." in next_action_text
    assert "Do not build decision rows yet." in next_action_text
    assert "validation commands" in next_action_text.lower()

    assert "Every new session begins with `docs/PROJECT_STATUS.md`." in status_policy_text
    assert "single required repository entrypoint" in status_policy_text
    assert "Every Codex task must update the canonical project status." in status_policy_text
    assert "Every Codex task must update the canonical next-action file." in status_policy_text
    assert "MASTER_DOCUMENT_INDEX.md" in status_policy_text
    assert "DOCUMENT_RETENTION_INDEX.md" in status_policy_text

    assert "entrypoint verification" in entrypoint_audit_text.lower()
    assert "supporting document ownership" in entrypoint_audit_text.lower()
    assert "duplicate ownership analysis" in entrypoint_audit_text.lower()
    assert "recommendations" in entrypoint_audit_text.lower()

    assert "Phase 4.5A defines the master market input specification." in roadmap_text
    assert "Phase 4.5B builds the universal feature registry." in roadmap_text
    assert "Phase 4.5C defines the universal math engine contracts." in roadmap_text
    assert "Phase 4.5D performs historical data acquisition" in roadmap_text
    assert "Phase 4.6 populates reusable historical features" in roadmap_text
    assert "Phase 4.7 constructs decision rows" in roadmap_text
    assert "docs/PROJECT_STATUS.md" in roadmap_text
    assert "docs/NEXT_ACTION.md" in roadmap_text
    assert "docs/STATUS_UPDATE_POLICY.md" in roadmap_text
    assert "docs/architecture/MASTER_MARKET_INPUT_SPECIFICATION.md" in roadmap_text
    assert "docs/architecture/HISTORICAL_RESEARCH_DATABASE.md" in roadmap_text

    assert "docs/PROJECT_STATUS.md" in master_index_text
    assert "docs/NEXT_ACTION.md" in master_index_text
    assert "docs/STATUS_UPDATE_POLICY.md" in master_index_text
    assert "docs/architecture/MASTER_MARKET_INPUT_SPECIFICATION.md" in master_index_text
    assert "docs/architecture/HISTORICAL_RESEARCH_DATABASE.md" in master_index_text

    assert "docs/reports/PROJECT_ENTRYPOINT_AUDIT.md" in retention_index_text
    assert "docs/reports/PROJECT_STATUS_GOVERNANCE_DISCOVERY.md" in retention_index_text
    assert "docs/reports/PHASE4_5A_MASTER_MARKET_INPUT_SPECIFICATION.md" in retention_index_text
    assert "docs/reports/PHASE4_4_EVENT_CENTRIC_HISTORICAL_ACQUISITION.md" in retention_index_text


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
