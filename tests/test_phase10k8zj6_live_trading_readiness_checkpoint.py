from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(name: str):
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(name)


def test_live_trading_readiness_docs_exist_and_state() -> None:
    docs = [
        ROOT / "PHASE10K8ZJ6_LIVE_TRADING_READINESS_CHECKPOINT.md",
        ROOT / "POST_LIVE_TRADING_READINESS_ARCHITECTURE_MAP_AFTER_10K8ZJ6.md",
        ROOT / "REMAINING_LIVE_TRADING_BLOCKERS_AFTER_10K8ZJ6.md",
        ROOT / "NEXT_PRODUCTION_ACTIVATION_PLAN_AFTER_10K8ZJ6.md",
    ]
    for path in docs:
        assert path.is_file(), path

    text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    for phrase in [
        "unified execution path remains canonical and disabled",
        "broker account boundary exists as metadata and readiness only",
        "credential policy exists without import-time secret reads",
        "reconciliation boundary exists but cannot execute",
        "ledger persistence plan remains local-only and deferred",
        "approval gate is documented but not activated",
        "No activation occurred",
        "Live trading remains disabled",
        "Broker account creation remains disabled",
        "Real order submission remains disabled",
    ]:
        assert phrase in text


def test_live_trading_readiness_modules_are_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    accounts = _fresh_import("src.brokerage.accounts")
    credentials = _fresh_import("src.brokerage.credentials")
    reconciliation = _fresh_import("src.brokerage.reconciliation")
    readiness = _fresh_import("src.brokerage.readiness")

    account_readiness = accounts.build_account_readiness(
        {"account_id": "acct-99", "broker_name": "demo"},
        credential_policy=credentials.BrokerCredentialPolicy(broker_name="demo", required_credentials=("api_key",)),
    )
    assert account_readiness.ready is False
    assert account_readiness.account_creation_allowed is False
    assert account_readiness.credentials_validation_allowed is False

    with pytest.raises(accounts.DisabledAccountCreationError):
        accounts.create_account_disabled({"account_id": "acct-99", "broker_name": "demo"})
    with pytest.raises(credentials.DisabledBrokerCredentialError):
        credentials.validate_broker_credentials_disabled({"broker_name": "demo", "credential_name": "api_key"})
    with pytest.raises(accounts.DisabledBrokerageError):
        reconciliation.reconcile_positions_disabled({"account_id": "acct-99"})

    order = brokerage.build_order_request({"ticker": "TEST", "stake": 10})
    plan = brokerage.build_execution_request(order)
    assert readiness.get_execution_readiness(order, execution_request=plan).ready is False
