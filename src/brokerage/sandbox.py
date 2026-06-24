"""Sandbox broker descriptor scaffold.

This module describes a sandbox-only broker shape without enabling any live
order submission, credential reads, or SDK/network behavior.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_text_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in values or () if value not in (None, ""))


@dataclass(frozen=True, slots=True)
class SandboxBrokerDescriptor:
    """Metadata-only sandbox broker descriptor."""

    sandbox_id: str
    broker_name: str
    sandbox_name: str = "disabled"
    sandbox_type: str = "sandbox"
    environment: str = "sandbox"
    approval_required: bool = True
    credentials_required: bool = False
    account_creation_allowed: bool = False
    live_trading_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxBrokerCapabilities:
    """Capabilities for a sandbox broker descriptor."""

    supports_accounts: bool = False
    supports_positions: bool = False
    supports_orders: bool = False
    supports_submit: bool = False
    supports_reconciliation: bool = False
    supports_ledger_persistence: bool = False
    sandbox_only: bool = True
    approval_required: bool = True
    credentials_required: bool = False
    live_trading_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxBrokerStatus:
    """Disabled sandbox broker readiness snapshot."""

    ready: bool
    status: str
    sandbox_descriptor: SandboxBrokerDescriptor
    capabilities: SandboxBrokerCapabilities
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    sandbox_boundary_disabled: bool = True
    live_trading_allowed: bool = False
    approval_required: bool = True
    credentials_required: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sandbox_descriptor"] = self.sandbox_descriptor.as_dict()
        payload["capabilities"] = self.capabilities.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def build_sandbox_descriptor(
    *,
    sandbox_id: str,
    broker_name: str,
    sandbox_name: str = "disabled",
    sandbox_type: str = "sandbox",
    environment: str = "sandbox",
    approval_required: bool = True,
    credentials_required: bool = False,
    account_creation_allowed: bool = False,
    live_trading_allowed: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxBrokerDescriptor:
    return SandboxBrokerDescriptor(
        sandbox_id=str(sandbox_id),
        broker_name=str(broker_name),
        sandbox_name=str(sandbox_name),
        sandbox_type=str(sandbox_type),
        environment=str(environment),
        approval_required=bool(approval_required),
        credentials_required=bool(credentials_required),
        account_creation_allowed=bool(account_creation_allowed),
        live_trading_allowed=bool(live_trading_allowed),
        metadata=dict(metadata or {}),
    )


def build_sandbox_capabilities(
    *,
    supports_accounts: bool = False,
    supports_positions: bool = False,
    supports_orders: bool = False,
    supports_submit: bool = False,
    supports_reconciliation: bool = False,
    supports_ledger_persistence: bool = False,
    sandbox_only: bool = True,
    approval_required: bool = True,
    credentials_required: bool = False,
    live_trading_allowed: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxBrokerCapabilities:
    return SandboxBrokerCapabilities(
        supports_accounts=bool(supports_accounts),
        supports_positions=bool(supports_positions),
        supports_orders=bool(supports_orders),
        supports_submit=bool(supports_submit),
        supports_reconciliation=bool(supports_reconciliation),
        supports_ledger_persistence=bool(supports_ledger_persistence),
        sandbox_only=bool(sandbox_only),
        approval_required=bool(approval_required),
        credentials_required=bool(credentials_required),
        live_trading_allowed=bool(live_trading_allowed),
        metadata=dict(metadata or {}),
    )


def build_sandbox_status(
    *,
    sandbox_id: str,
    broker_name: str,
    sandbox_name: str = "disabled",
    sandbox_type: str = "sandbox",
    environment: str = "sandbox",
    blockers: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxBrokerStatus:
    descriptor = build_sandbox_descriptor(
        sandbox_id=sandbox_id,
        broker_name=broker_name,
        sandbox_name=sandbox_name,
        sandbox_type=sandbox_type,
        environment=environment,
        metadata=metadata,
    )
    capabilities = build_sandbox_capabilities(metadata=metadata)
    blocker_items = (
        "sandbox_boundary_disabled",
        "approval_required",
        "credentials_not_required",
        "live_trading_disabled",
        *tuple(str(item) for item in blockers or () if item),
    )
    warning_items = _coerce_text_tuple(warnings)
    return SandboxBrokerStatus(
        ready=False,
        status="sandbox_disabled",
        sandbox_descriptor=descriptor,
        capabilities=capabilities,
        blockers=tuple(dict.fromkeys(blocker_items)),
        warnings=warning_items,
        sandbox_boundary_disabled=True,
        live_trading_allowed=False,
        approval_required=True,
        credentials_required=False,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "SandboxBrokerCapabilities",
    "SandboxBrokerDescriptor",
    "SandboxBrokerStatus",
    "build_sandbox_capabilities",
    "build_sandbox_descriptor",
    "build_sandbox_status",
]
