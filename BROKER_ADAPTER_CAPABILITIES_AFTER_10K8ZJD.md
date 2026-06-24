# Broker Adapter Capabilities After 10K8ZJD

- `supports_accounts`, `supports_positions`, `supports_orders`, and `supports_submit` remain disabled by default.
- `supports_reconciliation` and `supports_ledger_persistence` remain disabled by default.
- `supports_sandbox` remains enabled as metadata only.
- `requires_approval` and `requires_credentials` remain true in the disabled scaffold.
- `live_trading_allowed` remains false.
- The capability object is local metadata, not execution logic.
