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


def test_disabled_broker_account_boundary_docs_exist() -> None:
    docs = [
        ROOT / "PHASE10K8ZJ3_DISABLED_BROKER_ACCOUNT_BOUNDARY.md",
        ROOT / "BROKER_ACCOUNT_CONTRACTS_AFTER_10K8ZJ3.md",
        ROOT / "BROKER_CREDENTIAL_POLICY_AFTER_10K8ZJ3.md",
        ROOT / "BROKER_RECONCILIATION_DISABLED_BEHAVIOR_AFTER_10K8ZJ3.md",
    ]
    for path in docs:
        assert path.is_file(), path

    text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    for phrase in [
        "BrokerAccountDescriptor",
        "BrokerCredentialDescriptor",
        "BrokerCredentialPolicy",
        "AccountReadiness",
        "PositionReconciliationRequest",
        "PositionReconciliationResult",
        "DisabledAccountCreationError",
        "DisabledBrokerCredentialError",
        "create_account_disabled() always raises `DisabledAccountCreationError`",
        "validate_broker_credentials_disabled() always raises `DisabledBrokerCredentialError`",
        "reconcile_positions_disabled() always raises `DisabledBrokerageError`",
    ]:
        assert phrase in text


def test_disabled_broker_account_boundary_imports_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    accounts = _fresh_import("src.brokerage.accounts")
    credentials = _fresh_import("src.brokerage.credentials")
    reconciliation = _fresh_import("src.brokerage.reconciliation")

    assert accounts.BrokerAccountDescriptor.__module__ == "src.brokerage.accounts"
    assert credentials.BrokerCredentialDescriptor.__module__ == "src.brokerage.credentials"
    assert reconciliation.PositionReconciliationRequest.__module__ == "src.brokerage.reconciliation"

    with pytest.raises(accounts.DisabledAccountCreationError):
        accounts.create_account_disabled({"account_id": "acct-1", "broker_name": "demo"})
    with pytest.raises(credentials.DisabledBrokerCredentialError):
        credentials.validate_broker_credentials_disabled({"broker_name": "demo", "credential_name": "api_key"})
    with pytest.raises(accounts.DisabledBrokerageError):
        reconciliation.reconcile_positions_disabled({"account_id": "acct-1"})

    for module_name in ("src.brokerage.accounts", "src.brokerage.credentials", "src.brokerage.reconciliation"):
        source = Path(sys.modules[module_name].__file__).read_text(encoding="utf-8").lower()
        for banned in ("requests", "httpx", "yfinance", "selenium", "playwright", "alpaca", "robinhood", "ib_insync", "ccxt"):
            assert banned not in source
