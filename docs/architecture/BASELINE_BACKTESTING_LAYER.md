# Baseline Backtesting Layer

The baseline backtesting layer owns the first deterministic historical replay built only from certified decision rows.
It does not regenerate research assets, datasets, feature snapshots, mathematical engines, or signals.

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

## Contract

The first Phase 5.5 slice consumes only persisted, certified Phase 5.4 decision rows and the frozen certified evidence chain behind them.
Decision rows remain immutable historical evidence.
The backtesting layer replays those decisions against settled historical outcomes without changing the certified upstream inputs.

The layer must provide:

- deterministic replay
- historical result generation
- point-in-time validation
- performance metric calculation
- benchmark comparison
- reproducible backtest summaries
- persisted backtest artifacts
- dashboard-ready outputs

The layer must preserve:

- deterministic execution
- point-in-time safety
- lineage
- provenance
- certification
- reproducibility
- queryability

## Grain

The canonical baseline backtest grain is decision-row scoped and persists:

- `backtest_run_id`
- `backtest_row_id`
- `dataset_row_id`
- `decision_row_id`
- `decision_context_id`
- `source_signal_context_id`
- `scheduled_kickoff_time`
- `decision_cutoff_time`
- `market_type`
- `selection`
- `target_team_id`
- `opponent_team_id`
- `profit_loss_units`
- `transformation_version`

The first NFL slice replays 3 certified decision rows and materializes 3 persisted backtest rows plus one run summary.

## Point-In-Time Validation

All replay rows inherit the certified decision cutoff:

`decision_cutoff_time = scheduled_kickoff_time - 5 minutes`

The baseline backtesting layer validates that:

- the certified decision row is point-in-time safe
- the inherited cutoff remains before kickoff
- the dataset cutoff and kickoff match the certified historical dataset row
- settlement evidence is recorded after the cutoff
- signal-context market and selection values match the settled dataset row

The layer may reject rows, but it may not repair, reinterpret, or overwrite the upstream evidence.

## Settlement And Metrics

The first baseline engine settles:

- `moneyline`
- `spread`
- `total`

The deterministic replay persists:

- win / loss / push outcomes
- implied probability and expected value references
- profit and loss in 1-unit stake space
- ROI percent
- Brier score
- log loss
- benchmark comparisons against `no_trade` and market-implied expectation

## Artifacts And Queryability

The canonical local-first persistence owners are:

- `backtest_runs`
- `backtest_rows`

Each deterministic run also emits reproducible artifacts:

- `report.json`
- `summary.md`
- `dashboard.json`

Those artifacts remain tied to the backtest run, decision batch, dataset certification, and source lineage so downstream dashboards and audits can reconstruct the exact replay state.

## Validation And Readiness

The reusable baseline backtesting layer is ready only when:

- the decision layer is certified
- replay rows persist locally
- settlement alignment passes
- point-in-time validation passes
- benchmark outputs persist
- artifacts are reproducible
- the lifecycle state reaches `backtest_completed`

## Out Of Scope

- Research Intelligence
- Universal Market Framework expansion
- prediction markets
- options / 0DTE
- paper trading
- live execution
- machine learning
- optimization
- parameter tuning
