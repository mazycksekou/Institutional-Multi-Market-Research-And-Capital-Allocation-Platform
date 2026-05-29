# Sharp Sportsbook Adapter v1

## Summary

This release adds a read-only `sharp_sportsbook` provider adapter that is installed and safe by default.

- Provider remains disabled by default.
- Live reads remain disabled by default.
- Missing credentials never crash the app.
- Snapshot and health payloads stay compact and redacted.
- No betting, trading, or auto-execution paths are added.

## Environment Variables

- `SHARP_API_BASE_URL`
- `SHARP_API_KEY`
- `SHARP_API_TIMEOUT_SECONDS`
- `SHARP_PROVIDER_ENABLED`
- `SHARP_LIVE_READS_ENABLED`

## Safety Defaults

- `enabled=false` unless `SHARP_PROVIDER_ENABLED=true`
- `live_calls_enabled=false` unless both `SHARP_PROVIDER_ENABLED=true` and `SHARP_LIVE_READS_ENABLED=true`
- `provider_live_calls_enabled=false`
- `dry_run=true`
- `human_approval_required=true`
- `auto_bet_enabled=false`
- `auto_trade_enabled=false`
- `auto_execution_enabled=false`

## Gating Rules

Sharp snapshot reads are only attempted when all are true:

1. `SHARP_PROVIDER_ENABLED=true`.
2. `SHARP_LIVE_READS_ENABLED=true`.
3. `SHARP_API_KEY` exists.
4. Adapter remains read-only mode.

Otherwise the provider returns compact blocked or dry-run status:

- `provider_disabled`
- `live_reads_disabled`
- `blocked_missing_credentials`

When all gates are satisfied, the health status moves to `read_only_ready` while execution remains disabled.

## Read-only Network Policy

- Only HTTP `GET` is supported in live read path.
- Timeout is enforced via `SHARP_API_TIMEOUT_SECONDS`.
- Provider errors, rate limits, and malformed payloads are safely handled.
- No POST/PUT/PATCH/DELETE calls are present.

## Normalized Schema

Each normalized record contains:

- `provider_id`
- `provider_name`
- `received_at`
- `event_id`
- `sport`
- `league`
- `event_name`
- `start_time`
- `book`
- `market`
- `selection`
- `line`
- `odds`
- `decimal_odds`
- `implied_probability`
- `timestamp`
- `source_payload_redacted`
- `schema_version`

## API Endpoints

- `GET /api/providers/sharp/health`
- `POST /api/providers/sharp/snapshot`

Both endpoints return compact payloads and exclude secrets/raw auth data by default.
