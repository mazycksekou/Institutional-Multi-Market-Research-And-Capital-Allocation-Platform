# PHASE10K8ZJD Broker Adapter Protocol

## Scope
- Canonical execution path remains `src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> broker adapter boundary`.
- This phase adds a production-shaped adapter protocol only.
- No SDK imports, no network calls, no credentials, no account creation, and no live trading are enabled.

## Ownership
- `src.brokerage.adapter` owns the future adapter protocol and metadata descriptors.
- The adapter boundary is import-safe and disabled.
- The broker adapter boundary is not a separate paper-only path.

## Status
- `BrokerAdapter`, `BrokerAdapterDescriptor`, `BrokerAdapterCapabilities`, and `BrokerAdapterStatus` are metadata-only.
- `BrokerAccountInfo`, `BrokerPositionInfo`, and `BrokerOrderInfo` are local descriptors only.
- `DisabledBrokerAdapterError` documents the blocked live behavior.
- `build_adapter_descriptor()`, `build_adapter_capabilities()`, and `build_disabled_adapter_status()` stay local and deterministic.

## Required Statement
Only the final broker adapter scaffold is introduced in this phase. Real account creation, real-money trading, production deployment, and credential loading remain disabled.
