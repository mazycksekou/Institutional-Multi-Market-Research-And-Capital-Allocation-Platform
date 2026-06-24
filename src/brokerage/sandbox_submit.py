"""Sandbox submit flow scaffold.

The sandbox submit flow mirrors the production-shaped order/execution path but
remains disabled in this phase.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval import ApprovalState, evaluate_approval_gate
from .contracts import ExecutionRequest, OrderRequest
from .orders import build_execution_request, build_order_request
from .sandbox import SandboxBrokerDescriptor


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_approval_state(approval_state: ApprovalState | Mapping[str, Any]) -> ApprovalState:
    if isinstance(approval_state, ApprovalState):
        return approval_state
    if isinstance(approval_state, Mapping):
        return ApprovalState(
            approval_id=str(approval_state.get("approval_id") or approval_state.get("state_id") or "live_activation_state"),
            status=str(approval_state.get("status") or "disabled"),
            approved=bool(approval_state.get("approved", False)),
            denied=bool(approval_state.get("denied", False)),
            approval_scope=str(approval_state.get("approval_scope") or "live_activation"),
            approval_source=str(approval_state.get("approval_source") or "local"),
            metadata=dict(approval_state.get("metadata") or {k: v for k, v in approval_state.items() if v is not None}),
        )
    raise TypeError("approval_state must be an ApprovalState or mapping")


def _coerce_descriptor(descriptor: SandboxBrokerDescriptor | Mapping[str, Any]) -> SandboxBrokerDescriptor:
    if isinstance(descriptor, SandboxBrokerDescriptor):
        return descriptor
    if isinstance(descriptor, Mapping):
        return SandboxBrokerDescriptor(
            sandbox_id=str(descriptor.get("sandbox_id") or descriptor.get("adapter_id") or "sandbox"),
            broker_name=str(descriptor.get("broker_name") or descriptor.get("broker") or "unknown"),
            sandbox_name=str(descriptor.get("sandbox_name") or "disabled"),
            sandbox_type=str(descriptor.get("sandbox_type") or "sandbox"),
            environment=str(descriptor.get("environment") or "sandbox"),
            approval_required=bool(descriptor.get("approval_required", True)),
            credentials_required=bool(descriptor.get("credentials_required", False)),
            account_creation_allowed=bool(descriptor.get("account_creation_allowed", False)),
            live_trading_allowed=bool(descriptor.get("live_trading_allowed", False)),
            metadata=dict(descriptor.get("metadata") or {k: v for k, v in descriptor.items() if v is not None}),
        )
    raise TypeError("sandbox_descriptor must be a SandboxBrokerDescriptor or mapping")


@dataclass(frozen=True, slots=True)
class SandboxSubmitRequest:
    """Production-shaped sandbox submit request metadata."""

    submit_id: str
    order_request: OrderRequest
    execution_request: ExecutionRequest
    approval_state: ApprovalState
    sandbox_descriptor: SandboxBrokerDescriptor
    approval_gate_status: str = "disabled"
    sandbox_submit_allowed: bool = False
    live_trading_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["order_request"] = self.order_request.as_dict()
        payload["execution_request"] = self.execution_request.as_dict()
        payload["approval_state"] = self.approval_state.as_dict()
        payload["sandbox_descriptor"] = self.sandbox_descriptor.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxSubmitResult:
    """Disabled sandbox submit result snapshot."""

    submit_id: str
    request: SandboxSubmitRequest
    submitted: bool = False
    status: str = "disabled"
    blocked_reasons: tuple[str, ...] = ()
    message: str = "sandbox order submission is disabled"
    broker_order_id: str | None = None
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["metadata"] = dict(self.metadata)
        return payload


class DisabledSandboxSubmitError(RuntimeError):
    """Raised when sandbox order submission is requested while disabled."""


def build_sandbox_submit_request(
    order_request: OrderRequest | Mapping[str, Any] | None,
    *,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    approval_state: ApprovalState | Mapping[str, Any],
    sandbox_descriptor: SandboxBrokerDescriptor | Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> SandboxSubmitRequest:
    order = order_request if isinstance(order_request, OrderRequest) else build_order_request(order_request)
    execution = execution_request if isinstance(execution_request, ExecutionRequest) else build_execution_request(
        order,
        candidate=execution_request if isinstance(execution_request, Mapping) else None,
    )
    approval = _coerce_approval_state(approval_state)
    descriptor = _coerce_descriptor(sandbox_descriptor)
    gate = evaluate_approval_gate(approval)
    submit_id = str(execution.execution_id or order.order_id or "sandbox_submit")
    return SandboxSubmitRequest(
        submit_id=submit_id,
        order_request=order,
        execution_request=execution,
        approval_state=approval,
        sandbox_descriptor=descriptor,
        approval_gate_status=gate.status,
        sandbox_submit_allowed=False,
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )


def submit_sandbox_order_disabled(
    order_request: OrderRequest | Mapping[str, Any] | None,
    *,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    approval_state: ApprovalState | Mapping[str, Any],
    sandbox_descriptor: SandboxBrokerDescriptor | Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request = build_sandbox_submit_request(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        sandbox_descriptor=sandbox_descriptor,
        metadata=metadata,
    )
    result = SandboxSubmitResult(
        submit_id=request.submit_id,
        request=request,
        blocked_reasons=("sandbox_boundary_disabled", "live_trading_disabled"),
        metadata=dict(metadata or {}),
    )
    raise DisabledSandboxSubmitError(
        f"{result.message}; submit_id={result.submit_id}; approval_gate_status={request.approval_gate_status}"
    )


__all__ = [
    "DisabledSandboxSubmitError",
    "SandboxSubmitRequest",
    "SandboxSubmitResult",
    "build_sandbox_submit_request",
    "submit_sandbox_order_disabled",
]
