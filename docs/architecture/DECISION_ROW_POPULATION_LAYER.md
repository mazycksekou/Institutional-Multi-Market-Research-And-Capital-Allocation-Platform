# Decision Row Population Layer

The decision row population layer owns the first reusable, observation-only decision-row batch derived from certified signal outputs.
It does not create bets, trades, staking, bankroll decisions, order placement, portfolio allocation, or recommendations.

## Canonical Owners Reused

- `src.backtesting.decision_row_population`
- `src.market_intelligence.signal_population`
- `src.data.math_engine_population`
- `src.data.feature_registry`
- `src.data.historical_research_database`
- `src.data.research_asset_lifecycle_runtime`
- `src.storage.local_store`
- `src.data.nfl_p0_foundation`
- `src.services.streamlit_dashboard_data`

## Contract

The first Phase 5.4 slice consumes only persisted Phase 5.3 signal outputs and the certified signal summary.
The decision-row layer never rereads raw providers, normalized dataset tables, feature snapshots, mathematical-engine outputs, or signals.

The canonical decision asset remains observational and reusable across sports, prediction markets, options / 0DTE, and future market families.
Decision outputs may describe:

- expected value
- market state
- confidence
- consensus
- data quality
- freshness
- regime state
- other interpretable evidence

Decision rows must never prescribe:

- bets
- trades
- execution intent
- staking
- bankroll decisions
- portfolio allocation
- order placement
- recommendations

## Grain

The canonical decision-row grain is dataset-row scoped and inherits:

- `dataset_row_id`
- `decision_context_id`
- `source_signal_context_id`
- `scheduled_kickoff_time`
- `decision_cutoff_time`
- `decision_id`
- `decision_snapshot_context_id`
- `decision_version`
- `transformation_version`

The initial NFL slice materializes one reusable decision definition across 3 certified dataset contexts.
That produces 3 decision rows plus one summary row, all with deterministic identities, explicit lineage, and row-level alignment evidence.

## Point-In-Time Safety

All decision rows inherit the Phase 5.0 decision cutoff:

`decision_cutoff_time = scheduled_kickoff_time - 5 minutes`

Decision outputs may only use certified signal evidence that was already available at that cutoff.
The layer does not move the cutoff, infer a new one, or substitute later evidence.

## Registry

The first registered decision family is:

- `backtest_readiness`

The registry is intentionally small and portable:

- `deterministic_derived` decision rows apply fixed, stateless rules to certified signal outputs.
- Missingness is explicit and queryable.
- Decision rows remain immutable evidence records, not execution directives.

## Validation And Readiness

The reusable decision-row layer is ready only when:

- the signal layer is certified
- decision rows persist locally
- lineage is complete
- point-in-time validation passes
- the dataset certification remains intact
- the lifecycle state reaches `backtest_ready`

## Out Of Scope

- backtesting
- bankroll management
- live data ingestion
- paid provider integration
- machine learning
- trade or bet recommendations

