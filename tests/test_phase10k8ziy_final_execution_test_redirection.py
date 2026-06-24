from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_FILES = [
    ROOT / "tests" / "test_strategy_framework.py",
    ROOT / "tests" / "test_security_framework.py",
    ROOT / "tests" / "test_phase10k8zia_execution_scheduler_audit.py",
    ROOT / "tests" / "test_phase10k8zid_execution_final_delete_readiness.py",
    ROOT / "tests" / "test_phase10k8zig_execution_blocker_remediation_audit.py",
]


def test_final_execution_test_redirection_docs_exist() -> None:
    for path in [
        ROOT / "PHASE10K8ZIY_FINAL_EXECUTION_TEST_REDIRECTION.md",
        ROOT / "FINAL_EXECUTION_TEST_REDIRECTION_MAP_AFTER_10K8ZIY.md",
        ROOT / "FINAL_EXECUTION_TEST_COMPATIBILITY_REPORT_AFTER_10K8ZIY.md",
        ROOT / "FINAL_EXECUTION_TEST_DELETE_READINESS_AFTER_10K8ZIY.md",
    ]:
        assert path.is_file(), path


def test_final_execution_test_redirection_removed_wrapper_ownership() -> None:
    for path in TEST_FILES:
        text = path.read_text(encoding="utf-8")
        assert "src.brokerage.readiness" in text or "src/services/decision_engine" in text
        assert "automation_scheduler.execution_gatekeeper" not in text
        assert "automation_scheduler.execution_authorization" not in text
