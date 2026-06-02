# Kalshi Read-Only Local Setup

Use this check before running DeepSeek tiny provider settlement checks. It reports only safe booleans, env names, and readiness labels. It does not print API keys, private keys, signatures, raw provider payloads, or `.env` values.

## Command

```powershell
.\scripts\check_kalshi_readonly_ready.ps1
```

The default command makes zero provider calls.

Optional single read-only connectivity check:

```powershell
.\scripts\check_kalshi_readonly_ready.ps1 -TinyConnectivityCheck
```

Use the optional check only after the readiness report is `provider_ready`. It makes at most one harmless read-only market-list request and still reports no raw payloads or secrets.

## Required Env Names

- `KALSHI_PROVIDER_ENABLED`
- `KALSHI_LIVE_READS_ENABLED`
- `KALSHI_API_KEY`
- `KALSHI_API_SECRET`

Optional env names:

- `KALSHI_API_BASE_URL`
- `KALSHI_API_TIMEOUT_SECONDS`
- `KALSHI_MARKETS_PATH`
- `KALSHI_EVENTS_PATH`

## Report Fields

- `provider_readiness_status`
- `credentials_present`
- `live_reads_enabled`
- `provider_write=false`
- `execution_allowed=false`
- `missing_env_names`
- `disabled_env_names`
- `provider_readiness_blockers`
- `recommended_next_action`
- `raw_payload_included=false`
- `secrets_included=false`

## Safety

The readiness script never modifies `.env`, never enables provider writes, never places trades or orders, never persists outcomes, and never calls import or persist endpoints. It loads `.env` through the project Python environment when `python-dotenv` is available, but it only reports names and booleans.
