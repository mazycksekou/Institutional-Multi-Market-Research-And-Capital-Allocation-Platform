# Next Action

## Next Phase

`Phase 5.2 - Reusable Mathematical Engines`

## Previous Phase

`Phase 5.1B - Feature Snapshot Population` completed the first reusable NFL feature layer from the certified historical dataset batch and exposed feature readiness, lineage, certification, evidence-package, planner, dashboard, and NFL P0 reporting.

## Objective

Implement the first reusable, point-in-time-safe NFL mathematical engine layer from the certified feature snapshots and certified event context.
Reuse the canonical local-first storage, lineage, certification, lifecycle, coverage, and readiness owners without reopening optional enrichment assets as blockers.
Preserve deterministic mathematical-engine identities, feature-to-engine lineage, explicit missingness, and point-in-time safety from the certified feature layer upward.
Apply the minimum certified schema first rule: only the certified minimum-schema feature layer may block this phase, while future enrichment assets remain deferred.
Reuse the canonical evidence chain that now runs from certified research assets into certified historical dataset rows and then into certified feature snapshots.
Treat the certified schedule, results, odds, weather, injuries, team-statistics, and feature evidence as immutable inputs to the first reusable mathematical-engine layer.
Preserve the canonical connector-backed and canonical open-provider acquisition path already feeding the certified dataset and feature layers without introducing new connector work.
Do not ingest paid or live data, and do not begin signal population, decision rows, or backtesting in this phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, lifecycle runtime, feature registry, and feature snapshot population owners.
- Populate reusable mathematical-engine contracts and the first deterministic math outputs from the certified feature layer.
- Verify that mathematical-engine readiness is derived from certified feature evidence rather than hard-coded assumptions.
- Preserve dataset-batch references, dataset-row references, feature references, source certification references, and field-level provenance links.
- Preserve the canonical evidence chain without introducing a new connector, acquisition, dataset, or feature framework.
- Preserve the canonical connector-backed and canonical open-provider acquisition path without introducing new connector work.
- Update project status, roadmap, and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement new provider connectors.
- Do not implement signals, decision rows, or backtesting yet.
- Do not add provider-specific runtime ownership.
- Do not reopen player statistics, betting splits, officials, coaching, or other enrichment assets as blockers for the first feature layer.
- Do not generate decision rows yet.
- Do not backtest.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Reusable mathematical-engine implementation for the certified NFL minimum schema.
- Deterministic engine lineage linking certified feature snapshots and underlying certified dataset evidence.
- Mathematical-engine readiness, evidence packaging, and governance updates.

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
