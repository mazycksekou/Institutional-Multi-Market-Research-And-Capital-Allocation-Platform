# Phase 7 Operational Gap Report

Generated: 2026-06-12T15:11:53

- HEAD: `31706ee`
- Git clean: `True`

## Compile / Import Checks
- main import: `PASS`
- main compile: `PASS`
- action service compile: `PASS`
- betting action routes compile: `PASS`
- test support compile: `PASS`

## Main Route Slimming Check
- Direct `@app` route decorators in main.py: `0`

## Route Module Back-Import Check
- `src/api/*_routes.py` importing main.py: `0`

## Test Legacy Import Check
- Direct `from main import ...` in tests: `0`

## Analyze Event Ownership Check
- service_has_analyze_betting_event_pipeline: `True`
- route_imports_pipeline: `True`
- route_calls_pipeline: `True`
- test_uses_pipeline: `True`
- test_no_main_import: `True`

## API Route Count
- API_ROUTE_COUNT: `112`

## Phase 7 Initial Result
OVERALL_OK: `True`
No hard architectural failures found in Phase 7 baseline scan.
