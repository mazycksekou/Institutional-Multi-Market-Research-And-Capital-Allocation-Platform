from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_approval_gate_docs_exist_and_require_manual_approval() -> None:
    docs = [
        ROOT / "PHASE10K8ZJ5_PRODUCTION_APPROVAL_GATE_PLAN.md",
        ROOT / "LIVE_TRADING_APPROVAL_CHECKLIST_AFTER_10K8ZJ5.md",
        ROOT / "BROKER_ACTIVATION_REQUIREMENTS_AFTER_10K8ZJ5.md",
        ROOT / "PRODUCTION_DEPLOYMENT_BLOCKERS_AFTER_10K8ZJ5.md",
    ]
    for path in docs:
        assert path.is_file(), path

    text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    for phrase in [
        "Manual approval is required before live trading",
        "Required broker credentials are collected only after approval",
        "Required account creation happens only after approval",
        "Required live order-submit implementation happens only after approval",
        "Required position reconciliation happens only after approval",
        "Required ledger persistence happens only after approval",
        "Required production monitoring is mandatory",
        "Required rollback plan is mandatory",
        "Live trading remains disabled",
        "Account creation remains disabled",
        "Real order submission remains disabled",
    ]:
        assert phrase in text

