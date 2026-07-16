# Next Action

## Next Phase

`Phase 5.7 - Research Intelligence`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.6 - Validation And Hardening` certified the complete NFL research pipeline from the historical dataset through baseline backtesting. It added deterministic pipeline validation, normalized cross-layer dashboard contracts, persisted validation artifacts, and NFL P0 readiness for Research Intelligence on top of frozen, certified inputs.

## Objective

Build the first Research Intelligence layer on top of the certified and hardened NFL research pipeline.
Treat the certified and hardened NFL pipeline as immutable evidence while building Research Intelligence outputs.
Reuse only persisted certified evidence from the historical dataset, feature snapshots, mathematical engines, signals, decision rows, baseline backtests, and pipeline validation artifacts.
Preserve deterministic execution, point-in-time safety, lineage, provenance, certification, reproducibility, and queryability while synthesizing research outputs.
Treat the certified schedule, results, odds, weather, injuries, team-statistics, feature, math, signal, decision, baseline-backtest, and pipeline-validation evidence as immutable inputs to this phase.
Preserve the canonical local-first storage, dashboard, readiness, and validation owners without reopening acquisition or hardening scope unless a blocker is proven inside the certified evidence chain.
Do not ingest paid or live data, do not add new markets, and do not introduce paper trading or live execution in this phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, certification, lifecycle, feature registry, math engine population owners, reusable signal owners, decision-row owner, baseline-backtesting owner, and pipeline-validation owner.
- Build read-only research-intelligence summaries, query helpers, and dashboard-ready intelligence snapshots from the certified NFL evidence chain.
- Reuse persisted backtest metrics, benchmark comparisons, validation artifacts, and readiness snapshots as research inputs.
- Preserve dataset-batch references, dataset-row references, feature references, math references, signal references, decision references, backtest references, validation references, source certification references, and field-level provenance links.
- Preserve the canonical evidence chain without introducing a new connector, acquisition, dataset, feature, math, signal, decision, backtest, or pipeline-validation framework.
- Update project status, roadmap, and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement new provider connectors.
- Do not implement the Universal Market Framework.
- Do not implement prediction markets.
- Do not implement Zero-DTE options.
- Do not implement walk-forward validation yet.
- Do not implement paper trading yet.
- Do not implement live execution.
- Do not add additional markets.
- Do not add machine learning, optimization, or parameter tuning.
- Do not add provider-specific runtime ownership.
- Do not reopen player statistics, betting splits, officials, coaching, or other enrichment assets as blockers for Research Intelligence on the certified NFL path.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Deterministic Research Intelligence evidence built only from the certified NFL pipeline.
- Queryable research summaries that preserve lineage, provenance, certification, and point-in-time context.
- Dashboard-ready intelligence readiness reporting on top of the hardened NFL research engine path.

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
