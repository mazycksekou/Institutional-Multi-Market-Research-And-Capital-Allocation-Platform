# Ops Workflow

This project uses one verification layer for local, Codex, PowerShell, and Render-facing checks. The canonical workflow is Python-first; PowerShell scripts remain as optional Windows convenience wrappers.

## Canonical Python Validation

Use these commands on macOS, Linux, Windows, GitHub Actions, or Render-adjacent shells when you want the portable path:

```bash
python scripts/check_repo_preflight.py --start-task --include-ops
python scripts/check_root_markdown.py
python scripts/check_openapi_contract.py --output text
python scripts/check_architecture.py --output text
python scripts/check_audit_lifecycle.py
python scripts/check_document_lifecycle.py
python scripts/ops_check.py --mode local --output text --skip-network
python -m compileall src tests scripts
pytest -m smoke -q
```

Use the PowerShell wrappers below only when you want the Windows convenience layer.

## One-Time Setup

```powershell
cd "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration"
.\scripts\setup_dev.ps1
```

## Local Check

```powershell
.\scripts\check_local.ps1
```

Runs import, storage resolver, config, datasource, calibration, and safety checks without calling Render or providers.

## Render Check

```powershell
$env:APP_BASE_URL="https://betting-stock-api-code-integration.onrender.com"
.\scripts\check_render.ps1
```

Calls read-only Render endpoints only. It does not call the protected scheduled-run endpoint.

## Cron Check

```powershell
.\scripts\check_cron.ps1
```

Reads scheduled collector reports from `AUTOMATION_DATA_DIR` when available. Use `.\scripts\check_cron.ps1 -WithRender` to also run read-only Render endpoint checks.

## All Checks

```powershell
.\scripts\check_all.ps1
```

Runs local, Render, Cron, calibration, datasource, and safety checks. If `APP_BASE_URL` is not set, the wrapper uses the deployed project URL.

## Tests

```powershell
.\scripts\run_tests.ps1 -Mode quick
.\scripts\run_tests.ps1 -Mode full
.\scripts\run_tests.ps1 -Mode all
```

`pytest` is the standard runner. Existing `unittest` tests still run under pytest discovery. Raw `unittest` fallback is only used when explicitly requested:

```powershell
.\scripts\run_tests.ps1 -Mode full -FallbackUnittest
```

## Blocker Meanings

- `local_sandbox_network_unavailable`: the local runtime could not reach the network. This is an environment limitation, not a code defect.
- `render_endpoint_failure`: Render was reachable but an expected endpoint failed, returned malformed JSON, or returned an unexpected non-2xx status.
- `render_auth_problem`: a protected or authenticated endpoint returned 401 or 403.
- `provider_rate_limit`: the collector or reports include provider `http_429` blockers.
- `storage_problem`: storage read/write failed or Render storage is not using `/var/data`.
- `insufficient_settlement_data`: no matched outcomes are available for live calibration yet.
- `code_defect`: imports, JSON shape, required baseline, or other local code checks failed.
- `safety_failure`: execution or provider-write safety flags are enabled or nonzero.

## Report Paths

Ops reports are written under `AUTOMATION_DATA_DIR`:

```text
ops_checks/latest.json
ops_checks/items/<run_id>.json
ops_checks/daily/<YYYY-MM-DD>.json
ops_checks/daily/<YYYY-MM-DD>.md
```

If `AUTOMATION_DATA_DIR` is unset locally, reports use `data/ops_checks/`.

Reports never include API keys, tokens, authorization headers, `.env` content, signed URLs, raw provider payloads, or secret values. They only report whether keys are configured.
