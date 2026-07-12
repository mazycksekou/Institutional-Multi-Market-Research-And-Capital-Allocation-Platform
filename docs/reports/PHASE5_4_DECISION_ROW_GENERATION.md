# Phase 5.4 - Decision Row Generation

Phase 5.4 completed the first reusable NFL decision-row layer.
The implementation derives deterministic, observation-only decision rows from the certified Phase 5.3 signal layer and preserves point-in-time safety, lineage, certification, and dashboard visibility.

## Canonical Owners Reused

- `src.backtesting.decision_row_population`
- `src.market_intelligence.signal_population`
- `src.data.math_engine_population`
- `src.data.feature_registry`
- `src.data.historical_research_database`
- `src.data.historical_research_asset_certification_runtime`
- `src.data.research_asset_lifecycle_runtime`
- `src.storage.local_store`
- `src.data.nfl_p0_foundation`
- `src.services.streamlit_dashboard_data`

## Decision Row Families

The registry now contains one deterministic decision definition:

- `decision.sports.backtest_eligibility`

The first NFL batch materializes 3 decision rows plus one summary row from 3 certified dataset contexts.

## Implementation Summary

- Decision outputs are derived only from persisted signal rows and the certified signal summary.
- Decision rows preserve `dataset_row_id`, `decision_context_id`, `source_signal_context_id`, and the canonical game-level cutoff.
- Decision identities are deterministic and idempotent.
- Explicit missingness is preserved and queryable.
- Observation-only semantics are enforced at the registry and row layers.
- Row-level alignment evidence remains distinct for each decision context.
- The decision batch persists lineage, evidence-package references, and lifecycle state.
- The canonical lifecycle state is `backtest_ready`.

## Validation

The Phase 5.4 tests cover:

- registry completeness
- deterministic identities
- point-in-time inheritance
- observation-only semantics
- signal-input independence
- row-level alignment uniqueness
- dashboard reconstruction
- NFL P0 readiness surfacing

The full decision-chain validation passed on the final rerun; document lifecycle remains advisory with no clear violations.

## Senior Systems Engineer Review

### Strengths

- Reuses the canonical signal-output path instead of introducing a second decision framework.
- Keeps decision identity stable across reruns.
- Preserves reusable, cross-market decision semantics.

### Weaknesses

- The first slice is intentionally narrow and still depends on the earlier signal batch being complete.
- The decision family is intentionally small; richer decision taxonomies remain deferred.

### Implemented Improvements

- Added a dedicated decision row table to local storage.
- Added deterministic, observation-only decision-row population.
- Surfaced decision readiness in the NFL P0 dashboard snapshot.
- Preserved distinct row-level alignment evidence for each decision context.

### Deferred Improvements

- Broader decision families for later sports and market families.
- Additional summary analytics once downstream backtesting exists.

### Recommendation

Proceed to Phase 5.5 after the decision batch remains stable under rerun validation.

## Worldview / Research Query Engine Review

### Query Readiness

The batch is queryable by dataset row, decision context, decision id, decision family, and lifecycle state.

### Evidence Readiness

Each decision row retains source signal references, lineage references, and a deterministic evidence package.

### Experiment Readiness

The layer is ready for later experiment design, but it does not generate backtests.

### Unresolved Gaps

No blocking decision-layer gaps remain for the Phase 5.4 minimum slice.

### Recommendation

Use the certified decision layer as the immutable upstream input for Phase 5.5 baseline backtesting.

