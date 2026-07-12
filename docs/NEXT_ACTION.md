# Next Action

## Next Phase

`Phase 5.5 - Baseline Backtesting`

## Previous Phase

`Phase 5.4 - Decision Row Generation` completed the first reusable NFL decision-row layer from the certified signal outputs and certified event context. It exposed decision readiness, lineage, certification, evidence-package, planner, dashboard, and NFL P0 reporting.

## Objective

Implement the first reusable baseline NFL backtesting layer from the certified decision rows and frozen, certified inputs from the minimum-schema evidence chain.
Reuse the canonical local-first storage, lineage, certification, lifecycle, coverage, and readiness owners without reopening optional enrichment assets as blockers.
Preserve deterministic backtest identities, decision-to-backtest lineage, explicit missingness, and point-in-time safety from the certified decision layer upward.
Apply the minimum certified schema first rule: only the certified decision layer may block this phase, while future enrichment assets remain deferred.
Reuse the canonical evidence chain that now runs from certified research assets into certified historical dataset rows, certified feature snapshots, certified mathematical-engine outputs, certified signals, and certified decision rows.
Treat the certified schedule, results, odds, weather, injuries, team-statistics, feature, math, signal, and decision evidence as immutable inputs to the baseline backtesting layer.
Preserve the canonical connector-backed and canonical open-provider acquisition path already feeding the certified dataset, feature, math, signal, and decision layers without introducing new connector work.
Do not ingest paid or live data, and do not extend beyond baseline backtesting in this phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, lifecycle runtime, feature registry, math engine population owners, reusable signal owners, and decision-row owner.
- Populate reusable baseline backtest contracts and the first deterministic backtest rows from the certified decision layer.
- Verify that backtest readiness is derived from certified decision evidence rather than hard-coded assumptions.
- Preserve dataset-batch references, dataset-row references, feature references, math references, signal references, decision references, source certification references, and field-level provenance links.
- Preserve the canonical evidence chain without introducing a new connector, acquisition, dataset, feature, math, signal, or decision framework.
- Update project status, roadmap, and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement new provider connectors.
- Do not implement walk-forward validation yet.
- Do not implement paper trading yet.
- Do not implement live execution.
- Do not add provider-specific runtime ownership.
- Do not reopen player statistics, betting splits, officials, coaching, or other enrichment assets as blockers for baseline backtesting.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Reusable baseline backtest implementation for the certified NFL minimum schema.
- Deterministic backtest-row lineage linking certified decision rows and underlying certified evidence.
- Backtest readiness, evidence packaging, and governance updates.

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
