# Next Action

## Next Phase

`Phase 5.0 - Historical Dataset Population Layer`

## Previous Phase

`Phase 4.9H - NFL Team Statistics Research Asset Population` completed the final known minimum-schema NFL research asset and closed the required certified asset gap for the first baseline dataset path.

## Objective

Materialize the minimum-certified NFL historical dataset layer from the already certified schedule, results, odds, weather, injuries, and team-statistics assets.
Reuse the canonical local-first acquisition, certification, lifecycle, coverage, and readiness owners without reopening optional enrichment assets as blockers.
Preserve point-in-time-safe joins, immutable dataset lineage, deterministic reruns, evidence packaging, and readiness reporting.
Apply the minimum certified schema first rule: only the certified minimum-schema asset set may block this phase, while future enrichment assets remain deferred.
Reuse the canonical connector pattern that was already proven by the NFL schedule connector and the certified asset-population phases.
Preserve the canonical open-provider acquisition path that was established for `dataset.sports.nfl.schedule` and then reused across the certified NFL asset phases.
Do not ingest paid or live data, and do not begin feature engineering, mathematical engines, signal population, decision rows, or backtesting in this phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Integrate the certified minimum-schema NFL assets into one deterministic historical dataset population path.
- Verify that minimum-schema completeness is derived from certified evidence rather than hard-coded assumptions.
- Preserve raw-cache references, research-asset certification references, dataset certification references, and field-level provenance links.
- Preserve the canonical connector-backed acquisition pattern without introducing a new connector family.
- Update project status, roadmap, and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement new provider connectors.
- Do not implement mathematical engines yet.
- Do not add provider-specific runtime ownership.
- Do not reopen player statistics, betting splits, officials, coaching, or other enrichment assets as blockers for the first dataset layer.
- Do not implement feature engineering, mathematical engines, signals, decision rows, or backtesting yet.
- Do not generate decision rows yet.
- Do not backtest.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Historical dataset population implementation for the certified NFL minimum schema.
- Deterministic dataset-batch lineage linking certified schedule, results, odds, weather, injuries, and team-statistics assets.
- Dataset readiness, evidence packaging, and governance updates.

## Validation Commands

- `python -m compileall src tests scripts`
- `pytest -m smoke -q`
- `python scripts/check_root_markdown.py`
- `python scripts/check_openapi_contract.py --output text`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_audit_lifecycle.py`
- `python scripts/check_document_lifecycle.py --output text`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `python scripts/check_repo_preflight.py --before-commit --include-ops`
- `python scripts/check_repo_preflight.py --before-push --include-ops`
- `python scripts/check_repo_preflight.py --end-task --include-ops`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File .\\scripts\\run_tests.ps1 -Mode full`

## Reporting Rule

- The completion report must end with the next-step Codex prompt generated directly from the updated `docs/NEXT_ACTION.md`.
