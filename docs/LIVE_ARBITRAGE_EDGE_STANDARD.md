# LIVE ARBITRAGE EDGE STANDARD

`live_market_intelligence` is a read-only cross-sport intelligence layer for normalized odds snapshots, live-state snapshots, arbitrage detection, model-edge detection, alert serialization, replay certification, and safety reporting.

The standard never submits bets, orders, trades, swaps, deposits, withdrawals, transfers, or provider writes. All provider adapters expose only read-only fetch, validation, and normalization methods.

Safety floor:

- `provider_write=false`
- `execution_allowed=false`
- `execution_allowed_count=0`
- `live_execution_enabled=false`
- `auto_execution_enabled=false`
- `raw_payload_included=false`
- `raw_html_persisted=false`
- `raw_screenshot_persisted=false`
- `secrets_included=false`
