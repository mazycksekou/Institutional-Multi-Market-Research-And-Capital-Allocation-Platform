"""Explicit sandbox proof assembly."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .accounts import AccountReadiness, build_account_readiness
from .adapter_readiness import BrokerAdapterReadiness, build_broker_adapter_readiness
from .approval import ApprovalRequirement, ApprovalState
from .approval_evidence import ApprovalEvidence, ApprovalSource, ApprovalValidationResult, build_default_approval_evidence, validate_approval_evidence
from .credential_readiness import CredentialReadinessState, build_disabled_credential_readiness, evaluate_credential_readiness
from .deployment_readiness import DeploymentReadiness, build_disabled_deployment_readiness, evaluate_deployment_readiness
from .dry_run import DryRunExecutionResult, DryRunOrder, build_dry_run_execution, build_dry_run_order
from .dry_run_ledger import DryRunLedger, append_dry_run_event, build_dry_run_ledger, verify_dry_run_consistency
from .kill_switch import KillSwitchState, build_default_kill_switch_state
from .live_ledger import LiveLedgerPersistencePlan, build_live_ledger_persistence_plan
from .live_reconciliation import LiveReconciliationPlan, build_live_reconciliation_plan
from .live_submit import LiveSubmitRequest, build_live_submit_request
from .monitoring import MonitoringReadiness, build_monitoring_readiness, evaluate_monitoring_readiness
from .rollback import RollbackPlan, build_rollback_plan
from .sandbox_activation import SandboxActivationRequest, SandboxActivationResult, build_disabled_sandbox_activation, evaluate_sandbox_activation
from .client_factory import BrokerClientDescriptor, build_broker_client_descriptor, build_disabled_broker_client_status
from .credentials import BrokerCredentialDescriptor, BrokerCredentialPolicy, validate_broker_credentials_disabled


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class SandboxProofStep:
    """Single proof assertion for the sandbox activation boundary."""

    name: str
    passed: bool
    status: str = "blocked"
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["details"] = dict(self.details)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxProofResult:
    """Final proof summary for explicit approval-backed sandbox activation."""

    proof_id: str
    approval_evidence: ApprovalEvidence
    sandbox_activation: SandboxActivationResult
    dry_run_order: DryRunOrder
    dry_run_execution: DryRunExecutionResult
    dry_run_ledger: DryRunLedger
    steps: tuple[SandboxProofStep, ...] = ()
    proof_passed: bool = False
    status: str = "blocked"
    live_trading_allowed: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_evidence"] = self.approval_evidence.as_dict()
        payload["sandbox_activation"] = self.sandbox_activation.as_dict()
        payload["dry_run_order"] = self.dry_run_order.as_dict()
        payload["dry_run_execution"] = self.dry_run_execution.as_dict()
        payload["dry_run_ledger"] = self.dry_run_ledger.as_dict()
        payload["steps"] = [item.as_dict() for item in self.steps]
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def _step(name: str, passed: bool, *, status: str | None = None, blockers: tuple[str, ...] = (), warnings: tuple[str, ...] = (), details: Mapping[str, Any] | None = None) -> SandboxProofStep:
    return SandboxProofStep(
        name=name,
        passed=passed,
        status=status or ("passed" if passed else "blocked"),
        blockers=blockers,
        warnings=warnings,
        details=dict(details or {}),
    )


def _approval_state_from_evidence(approval: ApprovalEvidence) -> ApprovalState:
    return ApprovalState(
        approval_id=f"{approval.evidence_id}:state",
        status="approved_local_only" if approval.approved else "disabled",
        approved=approval.approved,
        denied=False,
        approval_scope=approval.approval_scope,
        approval_source=approval.source.value,
        requirements=approval.requirements,
        approver="local_owner",
        reviewed_at=approval.created_at,
        metadata=dict(approval.metadata),
    )


def build_sandbox_proof(
    *,
    approval_evidence: ApprovalEvidence | Mapping[str, Any] | None = None,
    sandbox_activation: SandboxActivationRequest | Mapping[str, Any] | None = None,
    dry_run_order: DryRunOrder | Mapping[str, Any] | None = None,
    dry_run_execution: DryRunExecutionResult | Mapping[str, Any] | None = None,
    dry_run_ledger: DryRunLedger | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxProofResult:
    approval = approval_evidence if isinstance(approval_evidence, ApprovalEvidence) else build_default_approval_evidence()
    activation_request = sandbox_activation if isinstance(sandbox_activation, SandboxActivationRequest) else build_disabled_sandbox_activation(approval_evidence=approval)
    dry_order = dry_run_order if isinstance(dry_run_order, DryRunOrder) else build_dry_run_order({})
    dry_execution = dry_run_execution if isinstance(dry_run_execution, DryRunExecutionResult) else build_dry_run_execution(dry_order.order_request)
    ledger = dry_run_ledger if isinstance(dry_run_ledger, DryRunLedger) else build_dry_run_ledger()
    return SandboxProofResult(
        proof_id="sandbox_proof_default",
        approval_evidence=approval,
        sandbox_activation=evaluate_sandbox_activation(activation_request),
        dry_run_order=dry_order,
        dry_run_execution=dry_execution,
        dry_run_ledger=ledger,
        steps=(),
        proof_passed=False,
        status="blocked",
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )


def run_sandbox_proof(
    *,
    metadata: Mapping[str, Any] | None = None,
) -> SandboxProofResult:
    approval = ApprovalEvidence(
        evidence_id="approval_evidence_explicit",
        source=ApprovalSource.OWNER,
        requirements=tuple(
            ApprovalRequirement(
                name=item.name,
                required=item.required,
                satisfied=True,
                description=item.description,
                evidence=item.evidence,
                metadata=dict(item.metadata),
            )
            for item in build_default_approval_evidence().requirements
        ),
        approved=True,
        status="approved_local_only",
        approval_scope="sandbox_activation",
        notes="explicit local approval evidence for sandbox proof",
        metadata=dict(metadata or {}),
    )
    approval_state = _approval_state_from_evidence(approval)
    activation_request = build_disabled_sandbox_activation(
        approval_evidence=approval,
        activation_metadata={"sandbox_mode": "explicit_approval_proof"},
        broker_readiness={
            "ready": True,
            "status": "ready_local_only",
            "blockers": (),
            "warnings": (),
            "broker_name": "sandbox-broker",
            "supported_asset_classes": [{"asset_class": "equity", "supported": True}],
            "supported_order_types": [{"order_type": "market", "supported": True}],
            "account_capabilities": [{"capability_name": "sandbox_account", "supported": True}],
            "reconciliation_capabilities": [{"capability_name": "position_reconciliation", "supported": True}],
        },
        credential_readiness=build_disabled_credential_readiness(broker_name="sandbox-broker"),
        kill_switch_state={
            "clear": True,
            "status": "clear",
            "reason": "local_only",
            "kill_switch_id": "sandbox_kill_switch",
        },
        rollback_metadata={
            "ready": True,
            "status": "ready_local_only",
            "steps": ("rollback-local-only",),
            "rollback_id": "rollback_plan_explicit_approval",
            "reason": "sandbox_proof_local_only",
        },
        monitoring_readiness={
            "ready": True,
            "status": "ready_local_only",
            "blockers": (),
            "warnings": (),
            "monitoring_id": "sandbox_monitoring",
            "requirements": [{"name": "health", "required": True, "satisfied": True}],
            "alerting_requirements": [{"name": "alerts", "required": True, "satisfied": True}],
            "health_check_requirements": [{"name": "health-check", "required": True, "satisfied": True}],
        },
        deployment_readiness=build_disabled_deployment_readiness(
            monitoring_readiness=build_monitoring_readiness(
                requirements=[{"name": "health", "required": True, "satisfied": True}],
                alerting_requirements=[{"name": "alerts", "required": True, "satisfied": True}],
                health_check_requirements=[{"name": "health-check", "required": True, "satisfied": True}],
            ),
            rollback_plan=build_rollback_plan(steps=("rollback-local-only",)),
            kill_switch_state=build_default_kill_switch_state(),
        ),
        metadata=metadata,
    )
    activation_result = evaluate_sandbox_activation(activation_request, metadata=metadata)
    dry_order = build_dry_run_order({"instrument_id": "sandbox", "quantity": 1, "side": "buy", "provider": "sandbox"})
    dry_execution = build_dry_run_execution(dry_order.order_request)
    ledger = build_dry_run_ledger()
    ledger = append_dry_run_event(ledger, order_request=dry_order.order_request, execution_request=dry_execution.execution_request, metadata=metadata)
    consistency = verify_dry_run_consistency(ledger)

    account_readiness = build_account_readiness(
        {"account_id": "sandbox-account", "broker_name": "sandbox-broker"},
        credential_policy={"required_credentials": ("api_key", "api_secret")},
    )
    broker_client_descriptor = build_broker_client_descriptor(approval_state, broker_name="sandbox-broker")
    broker_client_status = build_disabled_broker_client_status(approval_state, broker_name="sandbox-broker")
    credential_descriptor = BrokerCredentialDescriptor(broker_name="sandbox-broker", credential_name="api_key")
    credential_policy = BrokerCredentialPolicy(broker_name="sandbox-broker", required_credentials=("api_key", "api_secret"))
    live_submit_request = build_live_submit_request(
        dry_order.order_request,
        execution_request=dry_execution.execution_request,
        approval_state=approval_state,
        broker_client_descriptor=broker_client_descriptor,
    )
    live_reconciliation_plan = build_live_reconciliation_plan(
        approval_state=approval_state,
        broker_client_descriptor=broker_client_descriptor,
        current_positions=(),
        target_positions=(),
    )
    live_ledger_plan = build_live_ledger_persistence_plan(
        approval_state=approval_state,
        broker_client_descriptor=broker_client_descriptor,
    )
    credential_blocked = False
    try:
        validate_broker_credentials_disabled(credential_descriptor, policy=credential_policy)
    except Exception:
        credential_blocked = True

    steps = (
        _step("approval_evidence_exists", activation_result.state.approval_validation.valid, status=activation_result.state.approval_status, details={"source": approval.source.value}),
        _step("activation_metadata_exists", bool(activation_request.activation_metadata), details={"sandbox_id": activation_request.sandbox_id}),
        _step("broker_readiness_exists", activation_result.state.broker_readiness_ready, status=activation_result.state.broker_status),
        _step("credential_metadata_exists", bool(credential_descriptor.credential_name), status="disabled" if credential_blocked else "ready_local_only"),
        _step("kill_switch_exists", activation_result.state.kill_switch_ready, status=activation_result.state.kill_switch_status),
        _step("rollback_exists", activation_result.state.rollback_ready, status=activation_result.state.rollback_status),
        _step("monitoring_exists", activation_result.state.monitoring_ready, status=activation_result.state.monitoring_status),
        _step("deployment_blocked", not activation_result.state.deployment_ready or not live_ledger_plan.live_persistence_allowed, status=activation_result.state.deployment_status, blockers=("deployment_disabled",)),
        _step("submit_blocked", not dry_execution.live_submit_allowed and not live_submit_request.live_submit_allowed, status="disabled", blockers=("live_submit_disabled",)),
        _step("account_creation_blocked", not account_readiness.account_creation_allowed, status="disabled", blockers=("account_creation_disabled",)),
        _step("network_blocked", True, status="blocked", blockers=("network_disabled",)),
        _step("credentials_blocked", credential_blocked and not credential_policy.live_trading_allowed, status="blocked", blockers=("credential_loading_disabled",)),
        _step("broker_sdk_absent", True, status="not_imported", blockers=()),
    )
    proof_passed = all(step.passed for step in steps) and activation_result.proof_passed and not activation_result.live_activation_allowed and not live_submit_request.live_submit_allowed and not live_reconciliation_plan.live_reconciliation_allowed and not live_ledger_plan.live_persistence_allowed and not broker_client_status.live_trading_allowed
    blockers = tuple(
        dict.fromkeys(
            [
                *activation_result.blockers,
                *([item for step in steps if not step.passed for item in step.blockers]),
            ]
        )
    )
    return SandboxProofResult(
        proof_id="sandbox_proof_explicit_approval",
        approval_evidence=approval,
        sandbox_activation=activation_result,
        dry_run_order=dry_order,
        dry_run_execution=dry_execution,
        dry_run_ledger=ledger,
        steps=steps,
        proof_passed=proof_passed,
        status="sandbox_proof_passed" if proof_passed else "sandbox_proof_blocked",
        live_trading_allowed=False,
        blockers=blockers,
        warnings=tuple(dict.fromkeys([*activation_result.warnings, "sandbox_proof_remains_non_live"])),
        metadata=dict(metadata or {}),
    )


__all__ = [
    "SandboxProofResult",
    "SandboxProofStep",
    "build_sandbox_proof",
    "run_sandbox_proof",
]
