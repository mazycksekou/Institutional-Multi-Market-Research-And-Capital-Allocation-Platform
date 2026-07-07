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
    assert "Phase 4.4 — NFL Open Data Integration" in project_status_text
    assert "Phase 4.3.6 — Profile-Aware NFL P0 Validation" in project_status_text
    assert "Phase 4.3.7 — Minimum Backtest Row Contract" in project_status_text
    assert "latest validation status" in project_status_text
    assert "latest full gate result" in project_status_text
    assert "next recommended codex task" in project_status_text.lower()
    assert "docs/MASTER_ROADMAP.md" in project_status_text
    assert "docs/MASTER_DOCUMENT_INDEX.md" in project_status_text
    assert "docs/DOCUMENT_RETENTION_INDEX.md" in project_status_text

    assert "Phase 4.4 — NFL Open Data Integration" in next_action_text
    assert "Integrate the first free / open NFL data source against the minimum backtest row contract." in next_action_text
    assert "Do not ingest paid or live data." in next_action_text
    assert "Do not build features beyond the contract." in next_action_text
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

    assert "Phase 4.3.6 completed the profile-aware NFL P0 validation." in roadmap_text
    assert "Phase 4.3.7 defined the minimum backtest row contract." in roadmap_text
    assert "Phase 4.4 is the next recommended phase" in roadmap_text
    assert "docs/PROJECT_STATUS.md" in roadmap_text
    assert "docs/NEXT_ACTION.md" in roadmap_text
    assert "docs/STATUS_UPDATE_POLICY.md" in roadmap_text
    assert "docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md" in roadmap_text
    assert "docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md" in roadmap_text

    assert "docs/PROJECT_STATUS.md" in master_index_text
    assert "docs/NEXT_ACTION.md" in master_index_text
    assert "docs/STATUS_UPDATE_POLICY.md" in master_index_text
    assert "docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md" in master_index_text
    assert "docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md" in master_index_text

    assert "docs/reports/PROJECT_ENTRYPOINT_AUDIT.md" in retention_index_text
    assert "docs/reports/PROJECT_STATUS_GOVERNANCE_DISCOVERY.md" in retention_index_text
    assert "docs/reports/PROFILE_AWARE_NFL_P0_VALIDATION.md" in retention_index_text
    assert "docs/reports/NFL_P0_ARCHITECTURE_REUSE_AUDIT.md" in retention_index_text
    assert "docs/reports/NFL_BACKTEST_ROW_READINESS_CHECKLIST.md" in retention_index_text
    assert "docs/reports/NFL_DECISION_TIME_ALIGNMENT_RULES.md" in retention_index_text
    assert "docs/reports/NFL_BACKTEST_ROW_EXCLUSION_RULES.md" in retention_index_text
    assert "docs/reports/NFL_STREAMLIT_BACKTEST_READINESS_SPEC.md" in retention_index_text
    assert "docs/reports/NFL_WORLDVIEW_BACKTEST_READINESS_SPEC.md" in retention_index_text


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
