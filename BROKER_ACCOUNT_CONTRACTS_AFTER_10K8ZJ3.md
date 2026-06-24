# Broker Account Contracts After 10K8ZJ3

- `BrokerAccountDescriptor` is metadata only.
- `AccountReadiness` is disabled by default and keeps live trading disabled.
- `create_account_disabled()` always raises `DisabledAccountCreationError`.
- `build_account_readiness()` returns a disabled readiness snapshot.
- `AccountReadiness.account_creation_allowed` remains `False`.
- `AccountReadiness.credentials_validation_allowed` remains `False`.
