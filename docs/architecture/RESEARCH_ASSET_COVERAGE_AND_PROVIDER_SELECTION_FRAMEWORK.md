# Research Asset Coverage And Provider Selection Framework

This document is the canonical coverage-planning layer for research assets.
It is read-only. It does not download data, call providers, or mutate certified datasets.

## Purpose

The framework answers four questions for every research asset:

1. What is required?
2. What is already certified?
3. What is still missing?
4. Which provider or provider combination best closes the remaining gap?

The framework is coverage-driven, not provider-driven.
It exists so connector work can be prioritized by evidence instead of by convenience.

## Canonical Runtime Owner

- Runtime module: `src/market_intelligence/research_asset_coverage_planner.py`
- Shared dashboard wrapper: `src/services/streamlit_dashboard_data.py`
- Shared package export: `src/market_intelligence/__init__.py`

## Inputs

The planner reuses existing canonical owners:

- `src.data.historical_research_asset_certification_runtime`
- `src.data.research_asset_lifecycle_runtime`
- `src.data.data_source_registry`
- `src.data.nfl_open_data_sources`
- `src.data.nfl_open_data_source_exhaustion`
- `src.market_intelligence.nfl_coaching_sources`
- `src.storage.local_store`

## Planner Outputs

The planner produces:

- research asset coverage registry
- provider coverage registry
- coverage gap engine
- acquisition plan
- worldview query surface
- dashboard readiness snapshot

## Coverage Model

Each research asset is evaluated for:

- completion percentage
- missing components
- certification state
- lifecycle state
- readiness state
- quality score

The planner distinguishes:

- certified assets
- connector-upgrade assets
- missing assets
- future enrichment assets

## Provider Scoring

Each provider candidate is scored on:

- coverage
- historical depth
- point-in-time safety
- licensing
- reliability
- cost
- update frequency
- reproducibility
- certification suitability

The planner uses these scores to sort acquisition targets and recommend provider combinations.

## Acquisition Planning

The planner does not acquire data.
It emits acquisition plans only.

For the current NFL lane, the next missing minimum-schema target is:

- `dataset.nfl.team_stats_snapshots`

This remains the planner's first production connector target concept: the label always points at the highest-priority unresolved certified-coverage gap.

The schedule, results, odds, and weather assets now reuse the shared connector families and are certified. The planner therefore advances to team statistics rather than keeping completed assets as active gaps.

That first connector path served `dataset.sports.nfl.schedule`, which is why the planner can now advance beyond the schedule asset without losing the canonical open-provider acquisition pattern.

## Worldview And Query Readiness

The planner also documents the future query surface that a Research Query Engine or Worldview layer will need:

- which assets are missing
- which datasets are certified
- which providers remain unused
- why a dataset is blocked
- which certification failed
- what prevents a market from backtesting
- which connector would close a gap

The future query layer should read this planner output rather than infer coverage from provider names or file paths.

## Phase Relationship

- Phase 4.9A populates the NFL schedule research asset.
- Phase 4.9B builds this coverage planner and provider selection framework.
- Phase 4.9C will implement the first production connector for the NFL schedule asset.
- Phase 4.9C completed the first production connector for the NFL schedule asset.
- Phase 4.9D completed the NFL results research asset population.
- Phase 4.9E completed the NFL odds research asset population.
- Phase 4.9F completed the NFL weather research asset population.
- Phase 4.9G completed the NFL injuries research asset population.
- Phase 4.9H now focuses on the NFL team statistics research asset population.

## Reusability

The framework is designed to generalize to:

- MLB
- NBA
- NHL
- Prediction Markets
- Options / 0DTE
- futures
- crypto
- macro

The implementation should remain reusable by swapping the market profile and the certified minimum schema, not by copying planner logic.
