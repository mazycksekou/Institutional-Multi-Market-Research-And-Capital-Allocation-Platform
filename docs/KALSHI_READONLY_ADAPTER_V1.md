# Kalshi Read-Only Adapter V1

## Scope
- Provider ID: `kalshi_prediction_market`
- Provider type: `prediction_market`
- Mode: read-only, GET-only, dry-run-first
- Trading, order placement, and auto execution remain disabled

## Environment Variables
- `KALSHI_PROVIDER_ENABLED` (default: `false`)
- `KALSHI_LIVE_READS_ENABLED` (default: `false`)
- `KALSHI_API_BASE_URL`
- `KALSHI_API_KEY`
- `KALSHI_API_SECRET`
- `KALSHI_API_TIMEOUT_SECONDS`
- `KALSHI_MARKETS_PATH`
- `KALSHI_EVENTS_PATH`

## Safety Defaults
- `dry_run=true`
- `human_approval_required=true`
- `auto_bet_enabled=false`
- `auto_trade_enabled=false`
- `auto_execution_enabled=false`
- `kalshi_order_execution_enabled=false`

## Gating Rules
Kalshi polling runs only when all conditions pass:
- provider enabled
- live reads enabled
- credentials present
- dry run true
- auto execution false
- Kalshi order execution false

If gating fails, compact responses return safe blockers like:
- `provider_disabled`
- `live_reads_disabled`
- `missing_credentials`
- `dry_run_placeholder`
- `blocked_missing_credentials`

## Read-Only Network Behavior
- Live path uses GET only.
- No POST/PUT/PATCH/DELETE methods are used.
- Timeout and HTTP errors are mapped to safe blocker codes (`http_401`, `http_403`, `http_404`, `http_429`, `http_5xx`, `provider_timeout`).

## Normalized Prediction-Market Schema
- `provider_id`
- `provider_name`
- `received_at`
- `market_id`
- `event_id`
- `event_title`
- `contract_id`
- `contract_title`
- `ticker`
- `yes_bid`
- `yes_ask`
- `no_bid`
- `no_ask`
- `yes_price`
- `no_price`
- `implied_probability`
- `volume`
- `open_interest`
- `liquidity_score`
- `close_time`
- `status`
- `settlement_rule`
- `timestamp`
- `source_payload_redacted`
- `schema_version`

## Compact API Endpoints
- `GET /api/providers/kalshi/health`
- `POST /api/providers/kalshi/snapshot`

Default compact fields include:
- `ok`
- `status`
- `provider_id`
- `provider_enabled`
- `live_calls_enabled`
- `dry_run`
- `credential_status`
- `records_received`
- `records_valid`
- `records_rejected`
- `blockers`
- `rejection_reason_counts`
- `snapshot_path`

The default response does not include secrets, auth headers, raw provider payloads, or execution fields.
