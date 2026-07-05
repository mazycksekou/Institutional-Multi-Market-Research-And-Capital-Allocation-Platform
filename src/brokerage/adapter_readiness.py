"""Broker adapter readiness metadata scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_text_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in values or () if value not in (None, ""))


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
    for name in ("ready", "status", "blockers", "warnings", "metadata", "name", "required", "satisfied", "description", "asset_class", "order_type", "capability_name", "supported", "notes"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class BrokerCapabilityRequirement:
    name: str
    required: bool = True
    satisfied: bool = False
    description: str = ""
    evidence: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = list(self.evidence)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerAssetClassSupport:
    asset_class: str
    supported: bool = False
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerOrderTypeSupport:
    order_type: str
    supported: bool = False
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerAccountCapability:
    capability_name: str
    supported: bool = False
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerReconciliationCapability:
    capability_name: str
    supported: bool = False
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerAdapterReadiness:
    broker_name: str
    supported_asset_classes: tuple[BrokerAssetClassSupport, ...] = ()
    supported_order_types: tuple[BrokerOrderTypeSupport, ...] = ()
    account_capabilities: tuple[BrokerAccountCapability, ...] = ()
    reconciliation_capabilities: tuple[BrokerReconciliationCapability, ...] = ()
    requirements: tuple[BrokerCapabilityRequirement, ...] = ()
    ready: bool = False
    status: str = "disabled"
    live_trading_allowed: bool = False
    sandbox_allowed: bool = True
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["supported_asset_classes"] = [item.as_dict() for item in self.supported_asset_classes]
        payload["supported_order_types"] = [item.as_dict() for item in self.supported_order_types]
        payload["account_capabilities"] = [item.as_dict() for item in self.account_capabilities]
        payload["reconciliation_capabilities"] = [item.as_dict() for item in self.reconciliation_capabilities]
        payload["requirements"] = [item.as_dict() for item in self.requirements]
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def _coerce_requirement(requirement: BrokerCapabilityRequirement | Mapping[str, Any]) -> BrokerCapabilityRequirement:
    if isinstance(requirement, BrokerCapabilityRequirement):
        return requirement
    payload = _to_payload(requirement)
    return BrokerCapabilityRequirement(
        name=str(payload.get("name") or payload.get("requirement_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        evidence=_coerce_text_tuple(payload.get("evidence")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_asset_class_support(item: BrokerAssetClassSupport | Mapping[str, Any] | str) -> BrokerAssetClassSupport:
    if isinstance(item, BrokerAssetClassSupport):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("asset_class", item)
    return BrokerAssetClassSupport(
        asset_class=str(payload.get("asset_class") or payload.get("name") or "unknown"),
        supported=bool(payload.get("supported", False)),
        notes=str(payload.get("notes") or ""),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_order_type_support(item: BrokerOrderTypeSupport | Mapping[str, Any] | str) -> BrokerOrderTypeSupport:
    if isinstance(item, BrokerOrderTypeSupport):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("order_type", item)
    return BrokerOrderTypeSupport(
        order_type=str(payload.get("order_type") or payload.get("name") or "unknown"),
        supported=bool(payload.get("supported", False)),
        notes=str(payload.get("notes") or ""),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_account_capability(item: BrokerAccountCapability | Mapping[str, Any] | str) -> BrokerAccountCapability:
    if isinstance(item, BrokerAccountCapability):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("capability_name", item)
    return BrokerAccountCapability(
        capability_name=str(payload.get("capability_name") or payload.get("name") or "unknown"),
        supported=bool(payload.get("supported", False)),
        notes=str(payload.get("notes") or ""),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_reconciliation_capability(item: BrokerReconciliationCapability | Mapping[str, Any] | str) -> BrokerReconciliationCapability:
    if isinstance(item, BrokerReconciliationCapability):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("capability_name", item)
    return BrokerReconciliationCapability(
        capability_name=str(payload.get("capability_name") or payload.get("name") or "unknown"),
        supported=bool(payload.get("supported", False)),
        notes=str(payload.get("notes") or ""),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_broker_adapter_readiness(
    *,
    broker_name: str,
    supported_asset_classes: Sequence[BrokerAssetClassSupport | Mapping[str, Any] | str] | None = None,
    supported_order_types: Sequence[BrokerOrderTypeSupport | Mapping[str, Any] | str] | None = None,
    account_capabilities: Sequence[BrokerAccountCapability | Mapping[str, Any] | str] | None = None,
    reconciliation_capabilities: Sequence[BrokerReconciliationCapability | Mapping[str, Any] | str] | None = None,
    requirements: Sequence[BrokerCapabilityRequirement | Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BrokerAdapterReadiness:
    asset_support = tuple(_coerce_asset_class_support(item) for item in supported_asset_classes or ())
    order_support = tuple(_coerce_order_type_support(item) for item in supported_order_types or ())
    account_support = tuple(_coerce_account_capability(item) for item in account_capabilities or ())
    reconciliation_support = tuple(_coerce_reconciliation_capability(item) for item in reconciliation_capabilities or ())
    requirement_items = tuple(_coerce_requirement(item) for item in (requirements or ()))
    blockers = [
        "broker_adapter_readiness_disabled",
    ]
    if not broker_name:
        blockers.append("missing_broker_name")
    if not asset_support:
        blockers.append("missing_asset_class_support")
    if not order_support:
        blockers.append("missing_order_type_support")
    if not account_support:
        blockers.append("missing_account_capability_metadata")
    if not reconciliation_support:
        blockers.append("missing_reconciliation_capability_metadata")
    if requirement_items and any(not item.satisfied for item in requirement_items if item.required):
        blockers.append("unsatisfied_broker_capability_requirements")
    ready = not blockers or blockers == ["broker_adapter_readiness_disabled"]
    return BrokerAdapterReadiness(
        broker_name=str(broker_name),
        supported_asset_classes=asset_support,
        supported_order_types=order_support,
        account_capabilities=account_support,
        reconciliation_capabilities=reconciliation_support,
        requirements=requirement_items,
        ready=ready and bool(asset_support and order_support and account_support and reconciliation_support),
        status="ready_local_only" if ready and bool(asset_support and order_support and account_support and reconciliation_support) else "disabled",
        live_trading_allowed=False,
        sandbox_allowed=True,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=("broker_adapter_readiness_remains_disabled_in_this_phase",),
        metadata=dict(metadata or {}),
    )


def validate_broker_adapter_readiness(
    readiness: BrokerAdapterReadiness | Mapping[str, Any] | None = None,
    *,
    broker_name: str | None = None,
    supported_asset_classes: Sequence[BrokerAssetClassSupport | Mapping[str, Any] | str] | None = None,
    supported_order_types: Sequence[BrokerOrderTypeSupport | Mapping[str, Any] | str] | None = None,
    account_capabilities: Sequence[BrokerAccountCapability | Mapping[str, Any] | str] | None = None,
    reconciliation_capabilities: Sequence[BrokerReconciliationCapability | Mapping[str, Any] | str] | None = None,
    requirements: Sequence[BrokerCapabilityRequirement | Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BrokerAdapterReadiness:
    if isinstance(readiness, BrokerAdapterReadiness):
        return readiness
    if readiness is not None:
        payload = _to_payload(readiness)
        return build_broker_adapter_readiness(
            broker_name=str(payload.get("broker_name") or broker_name or "unknown"),
            supported_asset_classes=payload.get("supported_asset_classes") or supported_asset_classes,
            supported_order_types=payload.get("supported_order_types") or supported_order_types,
            account_capabilities=payload.get("account_capabilities") or account_capabilities,
            reconciliation_capabilities=payload.get("reconciliation_capabilities") or reconciliation_capabilities,
            requirements=payload.get("requirements") or requirements,
            metadata=dict(payload.get("metadata") or metadata or {}),
        )
    return build_broker_adapter_readiness(
        broker_name=str(broker_name or "unknown"),
        supported_asset_classes=supported_asset_classes,
        supported_order_types=supported_order_types,
        account_capabilities=account_capabilities,
        reconciliation_capabilities=reconciliation_capabilities,
        requirements=requirements,
        metadata=metadata,
    )


__all__ = [
    "BrokerAccountCapability",
    "BrokerAdapterReadiness",
    "BrokerAssetClassSupport",
    "BrokerCapabilityRequirement",
    "BrokerOrderTypeSupport",
    "BrokerReconciliationCapability",
    "build_broker_adapter_readiness",
    "validate_broker_adapter_readiness",
]
