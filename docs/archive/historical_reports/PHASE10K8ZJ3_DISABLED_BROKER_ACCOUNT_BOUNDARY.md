# Phase 10K8ZJ3 Disabled Broker Account Boundary

## Canonical Boundary

`src.brokerage.accounts`, `src.brokerage.credentials`, and `src.brokerage.reconciliation` define live-shaped account, credential, and reconciliation contracts without enabling live behavior.

## Required Symbols

- `BrokerAccountDescriptor`
- `BrokerCredentialDescriptor`
- `BrokerCredentialPolicy`
- `AccountReadiness`
- `PositionReconciliationRequest`
- `PositionReconciliationResult`
- `DisabledAccountCreationError`
- `DisabledBrokerCredentialError`
- `create_account_disabled`
- `validate_broker_credentials_disabled`
- `build_account_readiness`
- `build_reconciliation_request`
- `reconcile_positions_disabled`

## Disabled Behavior

create_account_disabled() always raises `DisabledAccountCreationError`.
validate_broker_credentials_disabled() always raises `DisabledBrokerCredentialError`.
reconcile_positions_disabled() always raises `DisabledBrokerageError`.
No import-time credential reads are allowed.
No broker SDK or network client is imported.
