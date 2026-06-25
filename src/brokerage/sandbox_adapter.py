"""Sandbox broker adapter metadata stub."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_text_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in values or () if value not in (None, ""))


def _coerce_named_tuple(values: Sequence[Any] | None, *, key: str) -> tuple[str, ...]:
    items: list[str] = []
    for item in values or ():
        if item in (None, ""):
            continue
        if isinstance(item, Mapping):
            items.append(str(item.get(key) or item.get("name") or item.get("capability_name") or item.get("asset_class") or item.get("order_type") or "unknown"))
        else:
            items.append(str(item))
    return tuple(items)


def _to_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "as_dict"):
        candidate = value.as_dict()
        if isinstance(candidate, Mapping):
            return dict(candidate)
    payload: dict[str, Any] = {}
    for name in (
        "adapter_id",
        "broker_name",
        "supported_asset_classes",
        "supported_order_types",
        "account_capabilities",
        "reconciliation_capabilities",
        "metadata",
        "status",
        "ready",
        "blockers",
        "warnings",
    ):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class SandboxBrokerCapabilities:
    """Metadata-only description of a sandbox broker adapter."""

    broker_name: str
    supported_asset_classes: tuple[str, ...] = ()
    supported_order_types: tuple[str, ...] = ()
    account_capabilities: tuple[str, ...] = ()
    reconciliation_capabilities: tuple[str, ...] = ()
    sandbox_allowed: bool = True
    live_trading_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["supported_asset_classes"] = list(self.supported_asset_classes)
        payload["supported_order_types"] = list(self.supported_order_types)
        payload["account_capabilities"] = list(self.account_capabilities)
        payload["reconciliation_capabilities"] = list(self.reconciliation_capabilities)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxBrokerAdapter:
    """Disabled sandbox broker adapter descriptor."""

    adapter_id: str
    broker_name: str
    capabilities: SandboxBrokerCapabilities
    status: str = "disabled"
    ready: bool = False
    sandbox_allowed: bool = True
    broker_connection_allowed: bool = False
    account_creation_allowed: bool = False
    order_submission_allowed: bool = False
    live_trading_allowed: bool = False
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["capabilities"] = self.capabilities.as_dict()
        payload["warnings"] = list(self.warnings)
        payload["blockers"] = list(self.blockers)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxBrokerResponse:
    """Result of evaluating the sandbox adapter metadata."""

    response_id: str
    adapter: SandboxBrokerAdapter
    ready: bool
    status: str
    blocked_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    sandbox_allowed: bool = True
    broker_connection_allowed: bool = False
    account_creation_allowed: bool = False
    order_submission_allowed: bool = False
    live_trading_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["adapter"] = self.adapter.as_dict()
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def _coerce_capabilities(capabilities: SandboxBrokerCapabilities | Mapping[str, Any] | None, *, broker_name: str) -> SandboxBrokerCapabilities:
    if isinstance(capabilities, SandboxBrokerCapabilities):
        return capabilities
    payload = _to_payload(capabilities)
    return SandboxBrokerCapabilities(
        broker_name=str(payload.get("broker_name") or broker_name or "sandbox-broker"),
        supported_asset_classes=_coerce_named_tuple(payload.get("supported_asset_classes"), key="asset_class"),
        supported_order_types=_coerce_named_tuple(payload.get("supported_order_types"), key="order_type"),
        account_capabilities=_coerce_named_tuple(payload.get("account_capabilities"), key="capability_name"),
        reconciliation_capabilities=_coerce_named_tuple(payload.get("reconciliation_capabilities"), key="capability_name"),
        sandbox_allowed=bool(payload.get("sandbox_allowed", True)),
        live_trading_allowed=bool(payload.get("live_trading_allowed", False)),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_sandbox_adapter(
    *,
    broker_name: str,
    supported_asset_classes: Sequence[str | Mapping[str, Any]] | None = None,
    supported_order_types: Sequence[str | Mapping[str, Any]] | None = None,
    account_capabilities: Sequence[str | Mapping[str, Any]] | None = None,
    reconciliation_capabilities: Sequence[str | Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxBrokerAdapter:
    """Build a disabled sandbox broker adapter descriptor."""

    capabilities = SandboxBrokerCapabilities(
        broker_name=broker_name,
        supported_asset_classes=_coerce_named_tuple(supported_asset_classes, key="asset_class"),
        supported_order_types=_coerce_named_tuple(supported_order_types, key="order_type"),
        account_capabilities=_coerce_named_tuple(account_capabilities, key="capability_name"),
        reconciliation_capabilities=_coerce_named_tuple(reconciliation_capabilities, key="capability_name"),
        sandbox_allowed=True,
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )
    return SandboxBrokerAdapter(
        adapter_id="sandbox_adapter_disabled",
        broker_name=broker_name,
        capabilities=capabilities,
        status="disabled",
        ready=False,
        sandbox_allowed=True,
        broker_connection_allowed=False,
        account_creation_allowed=False,
        order_submission_allowed=False,
        live_trading_allowed=False,
        warnings=("sandbox_adapter_remains_disabled_in_this_phase",),
        blockers=("sandbox_adapter_disabled",),
        metadata=dict(metadata or {}),
    )


def evaluate_sandbox_adapter(
    sandbox_adapter: SandboxBrokerAdapter | Mapping[str, Any] | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxBrokerResponse:
    """Evaluate sandbox adapter metadata locally."""

    if isinstance(sandbox_adapter, SandboxBrokerAdapter):
        adapter = sandbox_adapter
    else:
        payload = _to_payload(sandbox_adapter)
        capabilities = _coerce_capabilities(payload.get("capabilities"), broker_name=str(payload.get("broker_name") or "sandbox-broker"))
        adapter = SandboxBrokerAdapter(
            adapter_id=str(payload.get("adapter_id") or "sandbox_adapter_disabled"),
            broker_name=str(payload.get("broker_name") or capabilities.broker_name),
            capabilities=capabilities,
            status=str(payload.get("status") or "disabled"),
            ready=bool(payload.get("ready", False)),
            sandbox_allowed=bool(payload.get("sandbox_allowed", True)),
            broker_connection_allowed=bool(payload.get("broker_connection_allowed", False)),
            account_creation_allowed=bool(payload.get("account_creation_allowed", False)),
            order_submission_allowed=bool(payload.get("order_submission_allowed", False)),
            live_trading_allowed=bool(payload.get("live_trading_allowed", False)),
            warnings=_coerce_text_tuple(payload.get("warnings")),
            blockers=_coerce_text_tuple(payload.get("blockers")),
            metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
        )
    ready = bool(
        adapter.capabilities.broker_name
        and adapter.capabilities.supported_asset_classes
        and adapter.capabilities.supported_order_types
        and adapter.capabilities.account_capabilities
        and adapter.capabilities.reconciliation_capabilities
        and adapter.sandbox_allowed
    )
    blockers = tuple(
        dict.fromkeys(
            [
                *adapter.blockers,
                *(["missing_broker_name"] if not adapter.capabilities.broker_name else []),
                *(["missing_asset_class_support"] if not adapter.capabilities.supported_asset_classes else []),
                *(["missing_order_type_support"] if not adapter.capabilities.supported_order_types else []),
                *(["missing_account_capability"] if not adapter.capabilities.account_capabilities else []),
                *(["missing_reconciliation_capability"] if not adapter.capabilities.reconciliation_capabilities else []),
                "sandbox_adapter_disabled",
            ]
        )
    )
    status = "ready_local_only" if ready else "sandbox_adapter_blocked"
    response = SandboxBrokerResponse(
        response_id=f"{adapter.adapter_id}:response",
        adapter=adapter,
        ready=ready,
        status=status,
        blocked_reasons=blockers,
        warnings=tuple(dict.fromkeys([*adapter.warnings, "sandbox_adapter_remains_non_live"])),
        sandbox_allowed=True,
        broker_connection_allowed=False,
        account_creation_allowed=False,
        order_submission_allowed=False,
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )
    return response


__all__ = [
    "SandboxBrokerAdapter",
    "SandboxBrokerCapabilities",
    "SandboxBrokerResponse",
    "build_sandbox_adapter",
    "evaluate_sandbox_adapter",
]
