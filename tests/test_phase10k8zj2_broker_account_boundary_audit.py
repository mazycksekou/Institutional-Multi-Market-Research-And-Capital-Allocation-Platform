from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(name: str):
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(name)


def test_broker_account_boundary_audit_docs_exist_and_classify() -> None:
    docs = [
        ROOT / "PHASE10K8ZJ2_BROKER_ACCOUNT_BOUNDARY_AUDIT.md",
        ROOT / "BROKER_ACCOUNT_FILE_INVENTORY_AFTER_10K8ZJ2.md",
        ROOT / "BROKER_ACCOUNT_CREDENTIAL_RISK_MAP_AFTER_10K8ZJ2.md",
        ROOT / "BROKER_ACCOUNT_RUNTIME_RISK_MAP_AFTER_10K8ZJ2.md",
    ]
    for path in docs:
        assert path.is_file(), path

    text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    for phrase in [
        "BROKER_ACCOUNT_METADATA_ONLY",
        "BROKER_CREDENTIAL_RISK",
        "POSITION_RECONCILIATION_RISK",
        "LEDGER_PERSISTENCE_RISK",
        "MIGRATE_TO_SRC_SERVICES",
        "Broker account creation remains disabled",
        "Credential validation remains disabled",
        "Position reconciliation remains disabled",
        "Live order submission remains disabled",
    ]:
        assert phrase in text


def test_broker_account_boundary_modules_import_and_build_disabled_readiness(monkeypatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    accounts = _fresh_import("src.brokerage.accounts")
    credentials = _fresh_import("src.brokerage.credentials")
    reconciliation = _fresh_import("src.brokerage.reconciliation")

    assert brokerage.BrokerAccountDescriptor.__module__ == "src.brokerage.accounts"
    assert brokerage.BrokerCredentialDescriptor.__module__ == "src.brokerage.credentials"
    assert brokerage.PositionReconciliationRequest.__module__ == "src.brokerage.reconciliation"

    readiness = brokerage.build_account_readiness(
        {"account_id": "acct-1", "broker_name": "demo-broker"},
        credential_policy=brokerage.BrokerCredentialPolicy(
            broker_name="demo-broker",
            required_credentials=("api_key", "api_secret"),
        ),
    )
    assert readiness.ready is False
    assert readiness.live_trading_allowed is False
    assert readiness.account_creation_allowed is False
    assert readiness.credentials_validation_allowed is False
    assert "brokerage_boundary_disabled" in readiness.blockers

    request = brokerage.build_reconciliation_request(
        [{"instrument_id": "ABC", "quantity": 3}],
        [{"instrument_id": "ABC", "quantity": 5}],
        account_id="acct-1",
        broker_name="demo-broker",
    )
    assert request.account_id == "acct-1"
    assert request.current_positions[0].instrument_id == "ABC"
    assert request.target_positions[0].quantity == 5.0
