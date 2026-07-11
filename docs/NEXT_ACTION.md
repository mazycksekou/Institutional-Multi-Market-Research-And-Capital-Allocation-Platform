# Next Action

## Next Phase

`Phase 5.1 - Reusable Feature Population`

## Previous Phase

`Phase 5.0 - Historical Dataset Population Layer` completed the first deterministic, point-in-time-safe NFL historical dataset batch from the certified minimum-schema asset set and exposed dataset readiness, lineage, certification, evidence-package, planner, and dashboard reporting.

## Objective

Populate the first reusable, point-in-time-safe NFL feature layer from the certified historical dataset batch and certified event context.
Reuse the canonical local-first storage, lineage, certification, lifecycle, coverage, and readiness owners without reopening optional enrichment assets as blockers.
Preserve deterministic feature identities, feature snapshot timestamps, dataset-row lineage, explicit missingness, and point-in-time safety from the certified dataset layer upward.
Apply the minimum certified schema first rule: only the certified minimum-schema dataset layer may block this phase, while future enrichment assets remain deferred.
Reuse the canonical evidence chain that now runs from certified research assets into the certified historical dataset layer.
Treat the certified schedule, results, odds, weather, injuries, and team-statistics evidence as immutable inputs to the first reusable feature layer.
Preserve the canonical connector-backed and canonical open-provider acquisition path that already feeds the certified historical dataset layer without introducing new connector work.
Do not ingest paid or live data, and do not begin mathematical engines, signal population, decision rows, or backtesting in this phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Populate reusable feature snapshots from the certified historical dataset layer and certified event context.
- Verify that feature readiness is derived from certified dataset evidence rather than hard-coded assumptions.
- Preserve dataset-batch references, dataset-row references, source certification references, and field-level provenance links.
- Preserve the canonical evidence chain without introducing a new connector, acquisition, or dataset framework.
- Preserve the canonical connector-backed and canonical open-provider acquisition path without introducing new connector work.
- Update project status, roadmap, and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement new provider connectors.
- Do not implement mathematical engines yet.
- Do not add provider-specific runtime ownership.
- Do not reopen player statistics, betting splits, officials, coaching, or other enrichment assets as blockers for the first dataset layer.
- Do not implement mathematical engines, signals, decision rows, or backtesting yet.
- Do not generate decision rows yet.
- Do not backtest.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Reusable feature population implementation for the certified NFL minimum schema.
- Deterministic feature-snapshot lineage linking certified dataset rows and underlying certified source evidence.
- Feature readiness, evidence packaging, and governance updates.

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
