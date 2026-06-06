# LIVE MARKET PROVIDER CONTRACTS

Provider adapters may expose only these methods:

- `fetch_snapshot`
- `fetch_live_state`
- `fetch_market_catalog`
- `fetch_settlement_rules`
- `fetch_replay_snapshot`
- `validate_policy`
- `normalize_snapshot`

Adapters must not expose write-like or execution-like provider methods. Provider capabilities must declare source-policy decision, ingestion mode, latency expectations, supported sports, and supported market families.
