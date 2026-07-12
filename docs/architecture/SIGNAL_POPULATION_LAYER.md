# Signal Population Layer

The signal population layer owns the reusable observation-only signal batch that is derived from certified mathematical-engine outputs.
It does not create bets, trades, execution intent, bankroll decisions, order placement, or recommendations.

## Canonical Owners Reused

- `src.market_intelligence.signal_population`
- `src.data.math_engine_population`
- `src.data.historical_research_asset_certification_runtime`
- `src.data.research_asset_lifecycle_runtime`
- `src.storage.local_store`
- `src.data.nfl_p0_foundation`
- `src.services.streamlit_dashboard_data`

## Contract

The first Phase 5.3 slice consumes only persisted Phase 5.2 math-engine outputs and the certified math summary.
The signal layer never rereads raw providers, normalized dataset tables, feature snapshots, or decision-time alternatives.

The canonical signal asset remains observation-only and reusable across sports, prediction markets, options / 0DTE, and future market families.
Signals may describe:

- expected value
- market state
- confidence
- consensus
- data quality
- freshness
- regime state
- other interpretable evidence

Signals must never prescribe:

- bets
- trades
- execution intent
- staking
- bankroll decisions
- portfolio allocation
- order placement
- recommendations

## Grain

The canonical signal snapshot grain is dataset-row scoped and inherits:

- `dataset_row_id`
- `decision_context_id`
- `scheduled_kickoff_time`
- `decision_cutoff_time`
- `source_math_batch_id`
- `source_math_snapshot_ids`
- `signal_id`
- `signal_version`
- `transformation_version`

The initial NFL slice materializes 10 reusable signal definitions across 3 certified dataset contexts.
That produces 30 signal rows plus one summary row, all with deterministic identities and explicit lineage.

## Point-In-Time Safety

All signal outputs inherit the Phase 5.0 decision cutoff:

`decision_cutoff_time = scheduled_kickoff_time - 5 minutes`

Signals may only use certified math evidence that was already available at that cutoff.
The layer does not move the cutoff, infer a new one, or substitute later evidence.

## Registry

The first registered signal families are:

- market_context
- data_quality_context
- regime_context

The registry is intentionally small and portable:

- `direct` signals copy certified math outputs without reinterpretation.
- `deterministic_derived` signals apply fixed, stateless rules to certified math summaries.
- Missingness is explicit and queryable.

## Validation And Readiness

The reusable signal layer is ready only when:

- the math layer is certified
- signal rows persist locally
- lineage is complete
- point-in-time validation passes
- the dataset certification remains intact
- the lifecycle state reaches `signal_ready`

## Out Of Scope

- feature engineering
- decision rows
- backtesting
- live data ingestion
- paid provider integration
- machine learning
- recommendations

