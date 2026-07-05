# PHASE10K8ZIB Unified Brokerage Boundary

## Goal
Create production-shaped disabled brokerage contracts that future live trading
can reuse without changing upstream decision logic.

## Canonical symbols
- `DisabledBrokerageError`
- `DisabledExecutionError`
- `OrderSide`
- `OrderType`
- `OrderTimeInForce`
- `OrderStatus`
- `ExecutionMode`
- `OrderRequest`
- `ExecutionRequest`
- `ExecutionResult`
- `PositionSnapshot`
- `LedgerEvent`
- `ExecutionReadiness`
- `build_order_request`
- `build_execution_request`
- `record_ledger_event`
- `submit_order_disabled`
- `get_execution_readiness`

## Status
- Imports safely.
- No broker SDK imports.
- No network calls.
- No credential reads at import time.
- Broker submission remains disabled.

## Ownership
- `src.brokerage.orders` owns production-shaped order requests.
- `src.brokerage.execution` owns disabled submission behavior.
- `src.brokerage.ledger` owns local-only ledger events.
- `src.brokerage.readiness` owns disabled execution readiness.

