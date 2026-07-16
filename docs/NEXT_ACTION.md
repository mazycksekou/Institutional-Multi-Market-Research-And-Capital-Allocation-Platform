# Next Action

## Next Phase

`Phase 5.6 - Validation And Hardening`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.5 - Baseline Backtesting` completed the first deterministic replay of the certified `Phase 5.4 - Decision Row Generation` outputs against settled NFL history. It exposed persisted backtest rows, run summaries, benchmark comparisons, reproducible artifacts, dashboard-ready outputs, and NFL P0 backtest readiness from frozen, certified inputs.

## Objective

Validate and harden the production research engine path after the first reusable baseline NFL backtesting layer is complete.
Reuse the canonical local-first storage, lineage, certification, lifecycle, coverage, readiness, and baseline-backtesting owners without reopening optional enrichment assets as blockers.
Preserve deterministic backtest identities, decision-to-backtest lineage, explicit missingness, benchmark reproducibility, and point-in-time safety from the certified decision layer upward.
Apply the minimum certified schema first rule: only the certified backtest evidence chain may block this phase, while future enrichment assets remain deferred.
Reuse the canonical evidence chain that now runs from certified research assets into certified historical dataset rows, certified feature snapshots, certified mathematical-engine outputs, certified signals, certified decision rows, and persisted baseline backtests.
Treat the certified schedule, results, odds, weather, injuries, team-statistics, feature, math, signal, decision, and baseline-backtest evidence as immutable inputs to the hardening phase.
Preserve the canonical connector-backed and canonical open-provider acquisition path already feeding the certified dataset, feature, math, signal, decision, and backtest layers without introducing new connector work.
Do not ingest paid or live data, do not extend beyond baseline backtesting, and do not start Research Intelligence in this phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, lifecycle runtime, feature registry, math engine population owners, reusable signal owners, decision-row owner, and baseline-backtesting owner.
- Validate deterministic replay stability, point-in-time safety, persisted artifacts, benchmark calculations, and dashboard reconstruction from the certified decision layer.
- Verify that backtest readiness is derived from certified decision evidence rather than hard-coded assumptions.
- Preserve dataset-batch references, dataset-row references, feature references, math references, signal references, decision references, backtest references, source certification references, and field-level provenance links.
- Preserve the canonical evidence chain without introducing a new connector, acquisition, dataset, feature, math, signal, decision, or backtest framework.
- Update project status, roadmap, and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement new provider connectors.
- Do not implement Research Intelligence.
- Do not implement the Universal Market Framework.
- Do not implement prediction markets.
- Do not implement Zero-DTE options.
- Do not implement walk-forward validation yet.
- Do not implement paper trading yet.
- Do not implement live execution.
- Do not add machine learning, optimization, or parameter tuning.
- Do not add provider-specific runtime ownership.
- Do not reopen player statistics, betting splits, officials, coaching, or other enrichment assets as blockers for hardening the baseline backtesting path.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Validation and hardening evidence for the certified NFL baseline backtesting path.
- Deterministic backtest-row lineage linking certified decision rows and underlying certified evidence.
- Reproducibility, readiness, and governance updates for the production research engine path.

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
