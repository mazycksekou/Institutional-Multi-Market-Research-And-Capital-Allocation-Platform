# Live Market Intelligence

Read-only cross-sport live market intelligence standard for arbitrage detection, model-edge detection, source-policy gating, freshness validation, replay certification, and alert/report generation.

The package is intentionally non-executing:

- `provider_write=false`
- `execution_allowed=false`
- no sportsbook/provider account actions
- no raw HTML, screenshots, provider payloads, or secrets persisted

All fixtures are synthetic normalized facts.
