# Next Action

## Next Phase

`Phase 5.3 - Reusable Signals`

## Previous Phase

`Phase 5.2 - Reusable Mathematical Engines` completed the first reusable NFL mathematical-engine layer from the certified feature snapshots and exposed math readiness, lineage, certification, evidence-package, planner, dashboard, and NFL P0 reporting.

## Objective

Implement the first reusable, point-in-time-safe NFL signal layer from the certified mathematical-engine outputs and certified event context.
Reuse the canonical local-first storage, lineage, certification, lifecycle, coverage, and readiness owners without reopening optional enrichment assets as blockers.
Preserve deterministic signal identities, math-to-signal lineage, explicit missingness, and point-in-time safety from the certified math layer upward.
Apply the minimum certified schema first rule: only the certified math-engine layer may block this phase, while future enrichment assets remain deferred.
Reuse the canonical evidence chain that now runs from certified research assets into certified historical dataset rows, certified feature snapshots, and certified mathematical-engine outputs.
Treat the certified schedule, results, odds, weather, injuries, team-statistics, feature, and math evidence as immutable inputs to the first reusable signal layer.
Preserve the canonical connector-backed and canonical open-provider acquisition path already feeding the certified dataset, feature, and math layers without introducing new connector work.
Do not ingest paid or live data, and do not begin decision rows or backtesting in this phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, lifecycle runtime, feature registry, and math engine population owners.
- Populate reusable signal contracts and the first deterministic signals from the certified math layer.
- Verify that signal readiness is derived from certified math evidence rather than hard-coded assumptions.
- Preserve dataset-batch references, dataset-row references, feature references, math references, source certification references, and field-level provenance links.
- Preserve the canonical evidence chain without introducing a new connector, acquisition, dataset, feature, or math framework.
- Update project status, roadmap, and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement new provider connectors.
- Do not implement decision rows or backtesting yet.
- Do not add provider-specific runtime ownership.
- Do not reopen player statistics, betting splits, officials, coaching, or other enrichment assets as blockers for the first signal layer.
- Do not generate decision rows yet.
- Do not backtest.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Reusable signal implementation for the certified NFL minimum schema.
- Deterministic signal lineage linking certified mathematical-engine outputs and underlying certified feature evidence.
- Signal readiness, evidence packaging, and governance updates.

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
