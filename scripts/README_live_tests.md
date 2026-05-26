# Live Smoke Test Scripts

These scripts run compact live checks against:

`https://betting-stock-api-code-integration.onrender.com/api/actions/ticket/screenshot-analysis`

Set the API key before running:

```powershell
$env:ACTION_API_KEY = "your-action-api-key"
```

If `ACTION_API_KEY` is missing, the scripts print:

```text
ACTION_API_KEY is missing.
```

and exit with code `1`.

## Run One Sport

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\live_ncaaf_smoke.ps1
```

## Run Basketball Scripts

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\live_basketball_smoke.ps1
```

## Run All Current Active Sports

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\live_all_smoke.ps1
```

## Current Active Sport Scripts

- `live_nba_smoke.ps1`
- `live_nfl_smoke.ps1`
- `live_mlb_smoke.ps1`
- `live_soccer_smoke.ps1`
- `live_nhl_smoke.ps1`
- `live_tennis_smoke.ps1`
- `live_combat_smoke.ps1`
- `live_golf_smoke.ps1`
- `live_wnba_smoke.ps1`
- `live_ncaab_smoke.ps1`
- `live_ncaawb_smoke.ps1`
- `live_ncaaf_smoke.ps1`
- `live_f1_smoke.ps1`
- `live_nascar_smoke.ps1`
- `live_indycar_smoke.ps1`
- `live_motogp_smoke.ps1`
- `live_cricket_smoke.ps1`
- `live_cs2_smoke.ps1`
- `live_valorant_smoke.ps1`
- `live_lol_smoke.ps1`
- `live_dota2_smoke.ps1`
- `live_cod_smoke.ps1`

Each sport script runs three checks:

1. missing input safety
2. bad/text input safety
3. active model check

Each row prints compact fields for model status, calibration, probability, edge, confidence, decision, stake, confirmed count, same-selection no-bets, missing inputs, and pass/fail.

## Shared Files

- `live_helpers.ps1`: endpoint calls, compact table rows, board/logbook extraction, grouped pass/fail behavior
- `live_checks.ps1`: reusable assertions for active models, safe no-bets, and same-selection overlap
- `live_payloads.ps1`: reusable payload builders for every active sport
- `live_sport_template.ps1`: starter for future sports

## Developer Rule

Every future sport module must ship with:

1. direct model tests
2. screenshot normalization parity tests
3. registry `screenshot_alias_test_payload`
4. active live payload builder in `scripts/live_payloads.ps1`
5. `tests/test_live_smoke_payload_contract.py` coverage
6. a live smoke script in `scripts/live_<sport>_smoke.ps1`
7. missing input names printed on failure through the shared helpers
8. inclusion in `live_all_smoke.ps1` only after the local contract test passes

Future sports like esports and any later module should add a small payload builder in `live_payloads.ps1` and a short sport script based on `live_sport_template.ps1`. Do not paste long terminal blocks for live checks.

## Local Contract Check

Run this before adding a sport to `live_all_smoke.ps1`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_live_payload_contract.ps1
```

This does not call Render and does not require `ACTION_API_KEY`.
