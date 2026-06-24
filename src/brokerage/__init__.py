"""Canonical disabled brokerage boundary package."""

from .accounts import (
    AccountReadiness,
    BrokerAccountDescriptor,
    DisabledAccountCreationError,
    build_account_readiness,
    create_account_disabled,
)
from .approval import (
    ApprovalDecision,
    ApprovalGateStatus,
    ApprovalMissingError,
    ApprovalRejectedError,
    ApprovalRequirement,
    ApprovalState,
    build_default_approval_requirements,
    evaluate_approval_gate,
    require_live_approval,
)
from .client_factory import (
    BrokerClientDescriptor,
    BrokerClientFactoryStatus,
    DisabledBrokerClientError,
    build_broker_client_descriptor,
    build_disabled_broker_client_status,
    create_broker_client_disabled,
)
from .contracts import (
    DisabledBrokerageError,
    DisabledExecutionError,
    ExecutionMode,
    ExecutionReadiness,
    ExecutionRequest,
    ExecutionResult,
    LedgerEvent,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderTimeInForce,
    OrderType,
    PositionSnapshot,
)
from .credentials import (
    BrokerCredentialDescriptor,
    BrokerCredentialPolicy,
    DisabledBrokerCredentialError,
    validate_broker_credentials_disabled,
)
from .execution import build_disabled_execution_result, submit_order_disabled
from .kill_switch import KillSwitchState, KillSwitchTriggeredError, build_default_kill_switch_state, require_kill_switch_clear
from .ledger import clear_ledger_events, get_ledger_events, record_ledger_event
from .live_ledger import (
    LiveLedgerPersistenceDisabledError,
    LiveLedgerPersistencePlan,
    build_live_ledger_persistence_plan,
    persist_live_ledger_disabled,
)
from .live_reconciliation import (
    LiveReconciliationDisabledError,
    LiveReconciliationPlan,
    build_live_reconciliation_plan,
    reconcile_live_positions_disabled,
)
from .live_submit import (
    LiveSubmitDisabledError,
    LiveSubmitRequest,
    LiveSubmitResult,
    build_live_submit_request,
    submit_live_order_disabled,
)
from .orders import build_execution_request, build_order_request
from .positions import build_position_snapshot
from .reconciliation import (
    PositionReconciliationRequest,
    PositionReconciliationResult,
    build_reconciliation_request,
    reconcile_positions_disabled,
)
from .readiness import get_execution_readiness
from .rollback import RollbackPlan, build_rollback_plan
from .settlement import compare_settlement_rules

__all__ = [
    "AccountReadiness",
    "ApprovalDecision",
    "ApprovalGateStatus",
    "ApprovalMissingError",
    "ApprovalRejectedError",
    "ApprovalRequirement",
    "ApprovalState",
    "BrokerAccountDescriptor",
    "BrokerClientDescriptor",
    "BrokerClientFactoryStatus",
    "BrokerCredentialDescriptor",
    "BrokerCredentialPolicy",
    "DisabledAccountCreationError",
    "DisabledBrokerClientError",
    "DisabledBrokerCredentialError",
    "DisabledBrokerageError",
    "DisabledExecutionError",
    "ExecutionMode",
    "ExecutionReadiness",
    "ExecutionRequest",
    "ExecutionResult",
    "KillSwitchState",
    "KillSwitchTriggeredError",
    "LedgerEvent",
    "LiveLedgerPersistenceDisabledError",
    "LiveLedgerPersistencePlan",
    "LiveReconciliationDisabledError",
    "LiveReconciliationPlan",
    "LiveSubmitDisabledError",
    "LiveSubmitRequest",
    "LiveSubmitResult",
    "OrderRequest",
    "OrderSide",
    "OrderStatus",
    "OrderTimeInForce",
    "OrderType",
    "PositionReconciliationRequest",
    "PositionReconciliationResult",
    "PositionSnapshot",
    "RollbackPlan",
    "build_account_readiness",
    "build_broker_client_descriptor",
    "build_default_approval_requirements",
    "build_default_kill_switch_state",
    "build_disabled_broker_client_status",
    "build_disabled_execution_result",
    "build_execution_request",
    "build_live_ledger_persistence_plan",
    "build_live_reconciliation_plan",
    "build_live_submit_request",
    "build_order_request",
    "build_position_snapshot",
    "build_reconciliation_request",
    "build_rollback_plan",
    "compare_settlement_rules",
    "clear_ledger_events",
    "create_account_disabled",
    "create_broker_client_disabled",
    "evaluate_approval_gate",
    "get_execution_readiness",
    "get_ledger_events",
    "persist_live_ledger_disabled",
    "record_ledger_event",
    "reconcile_live_positions_disabled",
    "reconcile_positions_disabled",
    "require_kill_switch_clear",
    "require_live_approval",
    "submit_live_order_disabled",
    "submit_order_disabled",
    "validate_broker_credentials_disabled",
]
