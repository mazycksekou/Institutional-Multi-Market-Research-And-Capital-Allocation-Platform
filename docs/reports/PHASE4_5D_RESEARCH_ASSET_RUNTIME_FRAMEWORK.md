# Phase 4.5D - Research Asset Runtime Framework

## Summary

Phase 4.5D defines the runtime-facing research asset runtime framework.
It connects governed datasets, features, mathematical engines, signals, targets, confidence measures, decision rows, backtests, experiments, evidence packages, connectors, and validation results without creating a parallel runtime architecture.

The phase does not implement calculations or ingestion.
It standardizes how research assets relate to each other so future phases can reuse one canonical path.

## Existing Research Asset Abstractions Discovered

The repository already had the following reusable abstractions before this phase:

- `docs/architecture/MARKET_PROFILE_FRAMEWORK.md`
- `docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md`
- `docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md`
- `docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md`
- `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`
- `docs/architecture/RESEARCH_PLATFORM_ARCHITECTURE.md`
- `docs/MASTER_ROADMAP.md`
- `docs/MASTER_SYSTEM_ARCHITECTURE.md`
- `src.data`
- `src.storage`
- `src.core`
- `src.market_intelligence`
- `src.backtesting`
- `src.research`
- `src.analytics`
- `src.providers`
- `src.connectors`
- `src.data.validation`

These owners already define the market profile layer, the governing input layer, feature ownership, mathematical engine contracts, event-centric storage, research workspace boundaries, and validation helpers.

## Existing Abstractions Reused

This phase reuses the canonical owners above instead of inventing a parallel research asset system.

The reused pieces are:

- the market profile registry
- the master research engine specification
- the universal feature registry
- the universal mathematical engine contracts
- the event-centric historical research database
- the shared validation layer
- the shared storage layer
- the shared research workspace

## Research Asset Runtime Framework Created Or Extended

The new architecture doc defines the runtime-facing research asset runtime framework and the canonical dependency chain between:

- datasets
- features
- mathematical engines
- signals
- targets
- confidence measures
- decision rows
- backtests
- experiments
- evidence packages
- connectors
- validation results

## Research Asset Categories Documented

The framework now explicitly documents the following categories:

- dataset
- feature
- mathematical engine
- signal
- target
- confidence
- decision row
- backtest
- experiment
- evidence package
- connector
- validation result

## Runtime Dependency Framework Documented

The phase documents how the runtime chain works:

Provider -> Raw Acquisition Cache -> Integrity Validation -> Normalization -> Certification -> Historical Research Database -> Research Asset Runtime Framework -> Datasets -> Features -> Mathematical Engines -> Signals -> Targets -> Confidence -> Decision Rows -> Backtesting -> Experiments -> Evidence Packages

## Research Asset ID Standard Documented

The phase defines a permanent, dot-separated research asset ID standard.

Examples include:

- `dataset.nfl.games`
- `feature.sports.ticket_percentage`
- `math.options.gex`
- `signal.sports.reverse_line_movement`
- `target.options.primary_target`
- `connector.theoddsapi`
- `experiment.nfl.spread_model`
- `validation.dataset.certification`

## Lifecycle Framework Documented

Every research asset now follows the same lifecycle:

Defined -> Contract Ready -> Schema Ready -> Source Identified -> Connector Ready -> Historical Dataset Ready -> Math Ready -> Signal Ready -> Validated -> Backtested -> Production Ready

## Duplicate Systems Avoided

- No duplicate runtime owner was introduced.
- No duplicate storage engine was introduced.
- No duplicate validation layer was introduced.
- No duplicate feature registry was introduced.
- No duplicate mathematical registry was introduced.
- No duplicate historical database was introduced.
- No duplicate market profile system was introduced.
- No duplicate governance system was introduced.

## Engineering Improvements Implemented

- The repository now has an explicit research asset ID standard.
- The repository now has a canonical runtime asset ownership matrix.
- The repository now has an explicit minimum-schema-first rule for backtesting readiness.
- The repository now distinguishes research asset maturity from document count.
- The runtime connection chain is documented end-to-end.

## Engineering Improvements Deferred

The following improvements were evaluated but intentionally deferred:

- introducing a top-level Research Asset Registry
- creating new runtime modules for asset management
- implementing mathematical calculations
- implementing provider ingestion
- implementing feature pipelines
- implementing decision-row generation

These are better handled in later phases after the current contracts are fully reused.

## Senior Systems Engineer Review

Assessment:

- The framework is reusable and follows canonical ownership.
- The dependency chain is explicit enough to support later runtime implementation.
- The asset categories are broad enough for sports, prediction markets, and options / 0DTE without creating separate architectures.
- The minimum-schema-first rule reduces the risk of activating advanced assets before their evidence is mature.
- The main risk is catalog sprawl if future phases create too many overlapping inventories.

Recommendations:

1. Keep dataset ownership in `src.data` and `src.storage`.
2. Keep math ownership in `src.core`.
3. Keep evidence and study orchestration in `src.research` and `src.analytics`.
4. Introduce a Research Asset Registry only if the current docs begin to fragment the ownership model.

## Worldview Intelligence Review

This phase improves future Worldview compatibility by making research asset state, lineage, and evidence packaging explicit.

Worldview can now ask:

- which assets exist
- which assets are blocked
- which assets are ready for experiment generation
- which evidence package corresponds to an asset state
- which assets are limited by missing data, math, or validation

## Naming Review

The current `docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md` is now the canonical broader research-engine specification.

If the repository later needs an even broader top-level research asset registry, that should be handled as a separate future phase rather than another rename of this specification.

## PROJECT_STATUS updated

yes

## NEXT_ACTION updated

yes

## Readiness for Phase 4.7

The repository is ready for the next phase to acquire and certify the minimum certified historical dataset using the canonical acquisition framework.
