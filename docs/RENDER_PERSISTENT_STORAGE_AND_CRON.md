# Render Persistent Storage And Cron

This automation service uses file-backed runtime state. On Render, configure a persistent disk and route every runtime store through `AUTOMATION_DATA_DIR`.

Do not run the Kalshi collector script directly from a Render Cron Job when using file-backed state. The Cron Job should call the Web Service endpoint so the Web Service writes to its own persistent disk.

## Web Service Persistent Disk

1. Open the Render Web Service:
   `betting-stock-api-code-integration`

2. Add a Persistent Disk.

3. Set the mount path:
   `/var/data`

4. Set the Web Service environment variable:
   `AUTOMATION_DATA_DIR=/var/data`

5. Set the Web Service secret:
   `COLLECTOR_CRON_TOKEN=<secret>`

6. Redeploy the Web Service.

7. Verify storage health:

   ```bash
   curl -fsS https://betting-stock-api-code-integration.onrender.com/api/automation/health
   ```

   Expected storage fields:

   ```json
   {
     "env_var": "AUTOMATION_DATA_DIR",
     "data_dir": "/var/data",
     "backend": "file",
     "configured": true,
     "read_ok": true,
     "write_ok": true
   }
   ```

8. Run one scheduled collector endpoint call:

   ```bash
   curl -fsS -X POST "https://betting-stock-api-code-integration.onrender.com/api/automation/calibration-collector/scheduled-run" \
     -H "Content-Type: application/json" \
     -H "X-Collector-Token: $COLLECTOR_CRON_TOKEN" \
     -d "{\"trigger_type\":\"manual_storage_verification\",\"target_daily_new_contracts\":100,\"hard_cap_daily_new_contracts\":250,\"max_new_contracts_per_cycle\":25,\"max_markets_scanned\":5000,\"adaptive_throttle\":true}"
   ```

9. Confirm files are written under:

   ```text
   /var/data/outcomes/
   /var/data/paper_ledger/
   /var/data/review_queue/
   /var/data/collector_scheduler/
   /var/data/institutional_lab/
   /var/data/data_sources/
   /var/data/calibration/
   ```

10. Redeploy again.

11. Confirm files survive redeploy.

Do not claim durable calibration until paper decisions and explicit outcomes survive a redeploy or restart.

## Render Cron Job

Create a Render Cron Job that calls the Web Service endpoint.

Initial schedule:

```text
*/30 * * * *
```

Later, after clean provider behavior:

```text
*/15 * * * *
```

Cron environment variables:

```text
APP_BASE_URL=https://betting-stock-api-code-integration.onrender.com
COLLECTOR_CRON_TOKEN=<same secret as web service>
```

Cron command:

```bash
curl -fsS -X POST "$APP_BASE_URL/api/automation/calibration-collector/scheduled-run" \
  -H "Content-Type: application/json" \
  -H "X-Collector-Token: $COLLECTOR_CRON_TOKEN" \
  -d "{\"trigger_type\":\"render_cron\",\"target_daily_new_contracts\":100,\"hard_cap_daily_new_contracts\":250,\"max_new_contracts_per_cycle\":25,\"max_markets_scanned\":5000,\"adaptive_throttle\":true}"
```

Start at every 30 minutes because Kalshi recently returned `http_429`. Move to every 15 minutes only after clean runs. Do not run both Cron and a background worker unless lock and idempotency behavior are verified in production.

## Safety Controls

The scheduled endpoint must keep these controls false or zero:

```text
provider_write=false
execution_allowed_count=0
live_execution_enabled=false
auto_execution_enabled=false
kalshi_order_execution_enabled=false
sportsbook_bet_execution_enabled=false
broker_order_execution_enabled=false
actual_orders_submitted=0
actual_bets_submitted=0
actual_trades_submitted=0
```

The endpoint rejects live execution flags, provider-write flags, inferred-outcome flags, negative limits, and hard caps above `250`.
