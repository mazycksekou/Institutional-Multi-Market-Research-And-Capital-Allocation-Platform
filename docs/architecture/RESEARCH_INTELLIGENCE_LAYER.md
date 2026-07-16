# Research Intelligence Layer

The Research Intelligence layer owns deterministic explanatory synthesis on top of the certified NFL research pipeline.
It consumes persisted, certified evidence only and transforms that evidence into reproducible research summaries, rankings, evidence packages, and dashboard-ready intelligence views without mutating the underlying pipeline.

## Canonical Owners Reused

- `src.market_intelligence.research_intelligence`
- `src.backtesting.pipeline_validation`
- `src.backtesting.baseline_backtesting`
- `src.backtesting.decision_row_population`
- `src.market_intelligence.signal_population`
- `src.data.math_engine_population`
- `src.data.feature_registry`
- `src.data.historical_research_database`
- `src.data.nfl_p0_foundation`
- `src.services.streamlit_dashboard_data`
- `src.storage.local_store`

## Contract

The Phase 5.7 layer consumes only persisted, certified evidence from:

- historical dataset population
- feature snapshot population
- mathematical engine population
- signal population
- decision row population
- baseline backtesting
- pipeline validation and hardening

The layer must provide:

- evidence aggregation
- research summaries
- opportunity summaries
- historical comparison
- supporting evidence packages
- confidence explanations
- signal agreement summaries
- feature contribution summaries
- deterministic research reports
- dashboard-ready research views

The layer must preserve:

- deterministic execution
- point-in-time integrity
- lineage
- provenance
- certification
- reproducibility
- queryability

## Validation Surface

The canonical Research Intelligence snapshot checks that:

- pipeline validation remains certified and reaches `research_intelligence_ready`
- dataset, feature, math, signal, decision, and baseline-backtest layers retain their required certified or ready state
- settled backtest row count matches the persisted backtest sample size
- only replayed certified rows are consumed
- point-in-time validation remains true for every evidence package
- evidence package count and opportunity summary count remain aligned with the historical sample
- every evidence package preserves signal context and feature context
- dashboard-ready opportunity views preserve the full queryable research set
- the explicit `low_sample_size` warning remains visible as a warning-level check

## Artifacts And Queryability

Each deterministic Research Intelligence run persists reproducible artifacts under:

- `research_intelligence_artifacts/<research_intelligence_run_id>/report.json`
- `research_intelligence_artifacts/<research_intelligence_run_id>/summary.md`
- `research_intelligence_artifacts/<research_intelligence_run_id>/dashboard.json`

The layer also persists queryable rows in:

- `research_intelligence_runs`
- `research_intelligence_opportunities`

Those artifacts and tables remain tied to the certified dataset batch, feature batch, math batch, signal batch, decision batch, baseline backtest run, and pipeline validation run so downstream dashboards and audits can reconstruct the exact explanatory state.

## Readiness

The certified NFL research path is ready for the Universal Market Framework only when:

- every error-level Research Intelligence validation check passes
- persisted Research Intelligence artifacts remain present on disk
- signal, feature, decision, and backtest provenance remain attached to each historical opportunity
- the readiness state reaches `universal_market_framework_ready`

## Out Of Scope

- generating new signals
- altering mathematical outputs
- altering decision rows
- optimization
- parameter tuning
- execution recommendations
- capital allocation
- portfolio management
- additional markets
- paper trading
- live execution
- machine learning
