from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIT_EXECUTION_HELPER_FINAL_DELETE_PROOF.md",
    ROOT / "FINAL_EXECUTION_HELPER_IMPORT_SCAN_AFTER_10K8ZIT.md",
    ROOT / "FINAL_EXECUTION_HELPER_TEST_SCAN_AFTER_10K8ZIT.md",
    ROOT / "FINAL_EXECUTION_HELPER_DELETE_DECISION_AFTER_10K8ZIT.md",
]

WRAPPERS = [
    "settlement_rule_checker",
    "settlement_discovery",
    "audit_ledger",
    "institutional_audit_ledger",
    "strategy_performance_ledger",
    "broker_quality_scoring",
    "small_account_strategy",
    "manifold_no_bet_detector",
    "institutional_execution_desk",
]

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+automation_scheduler\.(?:%s)\b" % "|".join(WRAPPERS), re.M)


def test_final_delete_proof_docs_classify_all_wrappers_delete_ready() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "All nine wrapper-only execution helpers are `DELETE_READY_AFTER_PROOF`",
        "No active runtime import or active test import remains for those wrappers.",
        "Delete-ready:",
        "Blocked files: none.",
    ]:
        assert fragment in text
    for wrapper in WRAPPERS:
        assert wrapper in text


def test_final_delete_proof_scan_has_no_active_import_statements() -> None:
    offenders: list[str] = []
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if IMPORT_RE.search(text):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
