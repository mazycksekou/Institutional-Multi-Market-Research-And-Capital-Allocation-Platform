# Research Asset Runtime Framework

This document defines the runtime-facing framework that connects governed research assets together across the repository.
It is architecture only. It does not implement data ingestion, calculations, feature engineering, backtests, or live behavior.

The framework is reusable across sports, prediction markets, options / 0DTE, futures, crypto, and macro.
It exists to keep the repository local-first, certified-data-first, and reuse-first.

## Purpose

The framework answers one question: how do research assets connect together at runtime without creating duplicate ownership?

It keeps the following assets on one canonical path:

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

The framework does not replace the canonical owners already established by the repository.
It connects them.

## Relationship To Existing Canonical Owners

The framework is built on top of these existing layers:

- [Market Profile Framework](./MARKET_PROFILE_FRAMEWORK.md)
- [Master Research Engine Specification](./MASTER_RESEARCH_ENGINE_SPECIFICATION.md)
- [Universal Feature Registry](./UNIVERSAL_FEATURE_REGISTRY.md)
- [Universal Mathematical Engine Contracts](./UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md)
- [Historical Research Database](./HISTORICAL_RESEARCH_DATABASE.md)
- [Historical Dataset Acquisition Framework](./HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md)
- [Historical Dataset Acquisition Runtime](./HISTORICAL_DATASET_ACQUISITION_RUNTIME.md)
- [Research Asset Lifecycle Runtime](./RESEARCH_ASSET_LIFECYCLE_RUNTIME.md)
- [Research Platform Architecture](./RESEARCH_PLATFORM_ARCHITECTURE.md)

Those documents own market shape, governing inputs, feature lifecycle, math contract lifecycle, event-centric storage, and research workspace boundaries.
This framework owns the runtime relationship between those assets.

## Canonical Runtime Ownership By Asset Category

| Asset category | Canonical runtime owner | Notes |
| --- | --- | --- |
| Dataset | `src.data` and `src.storage` | Owns certified historical rows, versioning, lineage, and local storage shape. |
| Acquisition runtime | `src.data` and `src.storage` | Owns raw acquisition cache staging, integrity validation, and normalization/certification handoff. |
| Lifecycle runtime | `src.data` and `src.storage` | Owns immutable research asset identity, lifecycle state management, and time/entity alignment certification. |
| Feature | `src.data`, `src.market_intelligence`, and `src.core` | Owns reusable feature definitions and feature-ready runtime paths. |
| Mathematical engine | `src.core` | Owns reusable math, pricing, sizing, calibration, and probability primitives. |
| Signal | `src.market_intelligence` and `src.analytics` | Owns reusable signal derivation and signal-quality summaries. |
| Target | `src.backtesting` and `src.research` | Owns evaluation targets and future experiment targets. |
| Confidence | `src.analytics` and `src.research` | Owns confidence scoring, calibration summaries, and experiment gating. |
| Decision row | `src.backtesting` and `src.data` | Owns the generated research row built from event, market, selection, and feature snapshots. |
| Backtest | `src.backtesting` | Owns historical replay, evaluation, and result aggregation. |
| Experiment | `src.research` | Owns experiment metadata, study structure, and reproducibility artifacts. |
| Evidence package | `src.research` and `src.analytics` | Owns traceable result bundles and reviewable summaries. |
| Connector | `src.providers` and `src.connectors` | Owns source acquisition, adaptation, and normalization boundaries. |
| Validation result | `src.data.validation` and `scripts` | Owns checks, gating, and repo-level validation state. |

## Research Asset ID Standard

Every research asset must have one permanent, dot-separated identifier.

The identifier standard is:

`category.family.scope.name`

Examples:

- `dataset.nfl.games`
- `dataset.nfl.odds_snapshots`
- `feature.sports.ticket_percentage`
- `feature.options.gex`
- `math.options.gex`
- `math.sports.expected_value`
- `signal.sports.reverse_line_movement`
- `target.options.primary_target`
- `connector.theoddsapi`
- `experiment.nfl.spread_model`
- `validation.dataset.certification`

Rules:

- use lowercase
- separate segments with dots
- keep IDs stable across versions
- do not embed version numbers inside the ID
- do not reuse a retired ID for a different asset
- do not encode environment-specific paths or machine names in the ID

## Required Contract Dimensions

Every research asset entry must be able to report the following canonical fields:

- `Research Asset ID`
- `Asset Category`
- `Description`
- `Purpose`
- `Owner`
- `Dependencies`
- `Consumes`
- `Produces`
- `Lifecycle`
- `Versioning`
- `Validation Owner`
- `Storage Owner`
- `Profile Owner`
- `Runtime Owner`
- `Evidence Requirements`
- `Point-in-Time Rules`
- `Lineage Requirements`
- `Supported Markets`
- `Priority`

## Research Asset Lifecycle

Every research asset must support the same lifecycle state machine.
The asset may not advance to production without passing the earlier states.

Discovered -> Source Identified -> Connector Mapped -> Raw Acquired -> Integrity Verified -> Normalized -> Research Asset Certified -> Dataset Certified -> Feature Ready -> Math Ready -> Signal Ready -> Backtest Ready -> Production Ready

Lifecycle meaning:

- Discovered: the asset is known and cataloged.
- Source Identified: at least one usable source family is known.
- Connector Mapped: a canonical acquisition path exists.
- Raw Acquired: immutable source payloads have been staged.
- Integrity Verified: checksum, schema, and timestamp checks passed.
- Normalized: the raw payload has been normalized into governed shape.
- Research Asset Certified: the asset passed the asset-level certification gate.
- Dataset Certified: the dataset built from required assets has been certified.
- Feature Ready: the asset is ready for feature population.
- Math Ready: the asset is ready for governed mathematical engines.
- Signal Ready: the asset is ready for reusable signals.
- Backtest Ready: the asset is allowed into the minimum certified backtest path.
- Production Ready: the asset is usable in the canonical production workflow.

## Runtime Connection Chain

The framework connects research assets through one canonical sequence:

Provider -> Raw Acquisition Cache -> Integrity Validation -> Normalization -> Research Asset Certification -> Dataset Certification -> Historical Research Database -> Historical Dataset Acquisition Framework -> Historical Dataset Acquisition Runtime -> Historical Research Asset Certification Runtime -> Research Asset Lifecycle Runtime -> Datasets -> Features -> Mathematical Engines -> Signals -> Targets -> Confidence -> Decision Rows -> Backtesting -> Experiments -> Evidence Packages

The repository may define the complete research universe, but the first production backtests must still use only the certified minimum schema.
Advanced assets remain inactive until their data, math, and validation maturity are proven.

## Minimum-Schema-First Rule

The repository may define the complete research universe now.
That does not mean every asset is active now.

The minimum-schema-first rule is:

- first production backtests use only the certified minimum schema
- advanced metrics remain inactive until their data, math, and validation maturity are proven
- every new asset must declare the minimum data required before it can participate in backtesting
- evidence readiness matters more than document count

## Supported Markets

The framework supports the same market families as the repository-wide architecture:

- universal
- sports
- prediction markets
- options / 0DTE
- futures
- crypto
- macro

## Improvement Guidance

The framework should stay small and reuse existing owners.
If the catalog of datasets, features, mathematical engines, signals, targets, connectors, models, experiments, and evidence keeps growing, the repository may eventually want a single top-level Research Asset Registry to unify maturity tracking.

Do not create that registry during this phase.

## Worldview Compatibility

This framework improves future Worldview compatibility by making asset availability, lineage, and evidence packaging explicit.

Future Worldview requests should be able to ask:

- which assets exist
- which assets are missing
- which assets are blocked by missing data or math
- which assets are safe for objective experimentation
- which evidence package corresponds to a given asset state

## Out Of Scope

This framework does not:

- ingest data
- implement provider integrations
- implement mathematical formulas
- build feature pipelines
- build backtests
- build dashboards
- train models
- execute trades

It only defines the reusable runtime relationship between governed research assets.
