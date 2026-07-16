# Phase 5.5 - Baseline Backtesting

Phase 5.5 completed the first deterministic NFL historical backtesting layer from certified decision rows only.
The implementation replays the certified decision evidence against settled historical outcomes, preserves point-in-time safety and lineage, persists reproducible artifacts, and exposes dashboard-ready summaries without reopening upstream inputs.

## Canonical Owners Reused

- `src.backtesting.baseline_backtesting`
- `src.backtesting.decision_row_population`
- `src.market_intelligence.signal_population`
- `src.data.historical_research_database`
- `src.data.historical_research_asset_certification_runtime`
- `src.data.research_asset_lifecycle_runtime`
- `src.storage.local_store`
- `src.data.nfl_p0_foundation`
- `src.services.streamlit_dashboard_data`

## Backtest Scope

The first baseline run uses:

- certified decision rows only
- the frozen certified historical dataset row behind each decision
- the inherited decision cutoff from the certified decision layer

The first deterministic replay settles 3 certified decision rows across:

- `moneyline`
- `spread`
- `total`

## Implementation Summary

- Added the canonical `src.backtesting.baseline_backtesting` runtime for deterministic replay and persisted run reconstruction.
- Extended local storage with `backtest_runs` and `backtest_rows` persistence required for queryable replay evidence.
- Added point-in-time validation that checks cutoff inheritance, kickoff alignment, dataset-row alignment, and settlement timing.
- Added deterministic settlement logic for moneyline, spread, and total markets.
- Persisted benchmark comparisons against `no_trade` and market-implied expectation.
- Persisted reproducible `report.json`, `summary.md`, and `dashboard.json` artifacts for each deterministic run.
- Surfaced baseline-backtest readiness through the Streamlit data adapter and NFL P0 readiness snapshot.
- Hardened adjacent signal and decision lineage so the replay layer consumes canonical market context instead of summary-level placeholders.

## Validation

The Phase 5.5 tests cover:

- certified-decision-only admission control
- deterministic run identity and idempotent replay reuse
- point-in-time validation and settlement alignment
- persisted artifact creation
- dashboard reconstruction
- benchmark and summary calculation
- NFL P0 readiness surfacing
- adjacent signal and decision context alignment

The fixture replay settles 3 backtest rows with 2 wins, 1 loss, 0 pushes, and `20.0%` ROI.
The run emits a low-sample-size warning by design while still proving deterministic correctness and reproducible artifact generation.

## Senior Systems Engineer Review

### Strengths

- Keeps backtesting downstream of the certified decision layer instead of creating a parallel research path.
- Preserves deterministic replay identity and idempotent storage reuse.
- Produces queryable row-level evidence and run-level artifacts from the same canonical execution.

### Weaknesses

- The first replay slice is intentionally narrow and only exercises the minimum certified NFL schema.
- Sample size remains too small for any production-quality performance conclusion.

### Implemented Improvements

- Added canonical persisted backtest run and row storage.
- Added benchmark-ready and dashboard-ready replay summaries.
- Added row-level point-in-time validation and artifact lineage preservation.
- Corrected adjacent signal and decision market-context lineage to remove summary-level leakage risk.

### Deferred Improvements

- Larger certified historical samples.
- Walk-forward validation and stability studies.
- Cross-market expansion after the production research engine path is hardened.

### Recommendation

Proceed to Phase 5.6 to validate and harden the production research engine path before any Research Intelligence, paper trading, or live execution work.

## Worldview / Research Query Engine Review

### Query Readiness

Backtest runs are queryable by run id, decision batch, decision row, dataset row, market type, selection, outcome, and artifact path.

### Evidence Readiness

Each replay row retains certified decision references, source dataset references, benchmark context, point-in-time validation output, and persisted artifact lineage.

### Experiment Readiness

The layer is ready for deterministic hardening and later research-quality experiments, but it is not ready for strategy expansion or production conclusions.

### Unresolved Gaps

No blocking Phase 5.5 gaps remain inside the certified-decision replay scope.
The remaining work is Phase 5.6 hardening, not another expansion of market or intelligence scope.

### Recommendation

Use the completed baseline backtesting layer as the immutable evidence source for Phase 5.6 validation and hardening.
