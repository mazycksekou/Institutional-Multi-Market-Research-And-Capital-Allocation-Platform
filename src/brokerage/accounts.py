"""Disabled broker account boundary descriptors and readiness helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .contracts import DisabledBrokerageError, ExecutionMode


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class BrokerAccountDescriptor:
    """Local metadata descriptor for a future broker account."""

    account_id: str
    broker_name: str
    account_type: str = "brokerage"
    environment: str = "disabled"
    account_status: str = "disabled"
    margin_enabled: bool = False
    live_trading_enabled: bool = False
    cash_balance_hint: float | None = None
    buying_power_hint: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class AccountReadiness:
    """Disabled account-readiness snapshot for future live trading approval."""

    ready: bool
    status: str
    execution_mode: ExecutionMode = ExecutionMode.DISABLED
    account_descriptor: BrokerAccountDescriptor | None = None
    credential_policy: Any | None = None
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    brokerage_boundary_disabled: bool = True
    live_trading_allowed: bool = False
    account_creation_allowed: bool = False
    credentials_validation_allowed: bool = False
    account_required: bool = True
    credentials_required: bool = True
    approval_required: bool = True
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["execution_mode"] = str(self.execution_mode.value if isinstance(self.execution_mode, ExecutionMode) else self.execution_mode)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["account_descriptor"] = self.account_descriptor.as_dict() if self.account_descriptor is not None else None
        if self.credential_policy is not None and hasattr(self.credential_policy, "as_dict"):
            payload["credential_policy"] = self.credential_policy.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


class DisabledAccountCreationError(DisabledBrokerageError):
    """Raised when account creation is attempted against the disabled boundary."""


def _coerce_account_descriptor(account: BrokerAccountDescriptor | Mapping[str, Any] | None) -> BrokerAccountDescriptor | None:
    if account is None:
        return None
    if isinstance(account, BrokerAccountDescriptor):
        return account
    if not isinstance(account, Mapping):
        return None
    return BrokerAccountDescriptor(
        account_id=str(account.get("account_id") or account.get("broker_account_id") or account.get("id") or "unknown"),
        broker_name=str(account.get("broker_name") or account.get("broker") or account.get("provider") or "unknown"),
        account_type=str(account.get("account_type") or "brokerage"),
        environment=str(account.get("environment") or account.get("mode") or "disabled"),
        account_status=str(account.get("account_status") or account.get("status") or "disabled"),
        margin_enabled=bool(account.get("margin_enabled", False)),
        live_trading_enabled=bool(account.get("live_trading_enabled", False)),
        cash_balance_hint=account.get("cash_balance_hint"),
        buying_power_hint=account.get("buying_power_hint"),
        metadata=dict(account.get("metadata") or {k: v for k, v in account.items() if v is not None}),
    )


def build_account_readiness(
    account: BrokerAccountDescriptor | Mapping[str, Any] | None = None,
    *,
    credential_policy: Any | None = None,
    execution_mode: ExecutionMode | str = ExecutionMode.DISABLED,
    allow_live: bool = False,
    extra_blockers: Sequence[str] | None = None,
    extra_warnings: Sequence[str] | None = None,
) -> AccountReadiness:
    descriptor = _coerce_account_descriptor(account)
    if isinstance(execution_mode, ExecutionMode):
        mode = execution_mode
    else:
        mode_text = str(execution_mode or "").strip().lower()
        mode = ExecutionMode(mode_text) if mode_text in ExecutionMode._value2member_map_ else ExecutionMode.DISABLED

    blockers = [
        "brokerage_boundary_disabled",
        "live_trading_deferred",
        "account_creation_disabled",
        "credential_validation_disabled",
    ]
    warnings = [
        "disabled_account_boundary_only",
    ]
    if descriptor is None:
        blockers.append("missing_account_descriptor")
    if credential_policy is None:
        blockers.append("missing_credential_policy")
    if not allow_live:
        blockers.append("allow_live_false")
    if extra_blockers:
        blockers.extend(str(item) for item in extra_blockers if item)
    if extra_warnings:
        warnings.extend(str(item) for item in extra_warnings if item)

    return AccountReadiness(
        ready=False,
        status="disabled" if mode == ExecutionMode.DISABLED else "live_trading_deferred",
        execution_mode=mode,
        account_descriptor=descriptor,
        credential_policy=credential_policy,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        brokerage_boundary_disabled=True,
        live_trading_allowed=False,
        account_creation_allowed=False,
        credentials_validation_allowed=False,
        account_required=True,
        credentials_required=True,
        approval_required=True,
        metadata={"allow_live_requested": bool(allow_live)},
    )


def create_account_disabled(
    account: BrokerAccountDescriptor | Mapping[str, Any] | None = None,
    *,
    credential_policy: Any | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    descriptor = _coerce_account_descriptor(account)
    broker_name = descriptor.broker_name if descriptor is not None else "unknown"
    account_id = descriptor.account_id if descriptor is not None else "unknown"
    message = reason or "broker account creation is disabled until live trading approval is explicitly granted"
    raise DisabledAccountCreationError(
        f"{message}; broker={broker_name}; account_id={account_id}; credential_policy={bool(credential_policy is not None)}"
    )


__all__ = [
    "BrokerAccountDescriptor",
    "AccountReadiness",
    "DisabledAccountCreationError",
    "build_account_readiness",
    "create_account_disabled",
]
