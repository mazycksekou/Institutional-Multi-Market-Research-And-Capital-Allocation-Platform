# Universal Feature Registry

This document is the canonical registry layer for reusable research features across every market family in the repository.

It sits above the [Master Research Engine Specification](./MASTER_RESEARCH_ENGINE_SPECIFICATION.md) and below the detailed catalogs in `docs/catalogs/`.
It does not implement feature engineering, signals, targets, providers, or backtests.
Do not implement providers, feature engineering, or backtests in this layer.
It defines the reusable feature ownership model and lifecycle rules that all future markets share.

## Canonical Owners Reused

- `docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md`
- `docs/catalogs/COMPLETE_FEATURE_CATALOG.md`
- `docs/catalogs/COMPLETE_METRIC_CATALOG.md`
- `docs/catalogs/FEATURE_DEPENDENCY_GRAPH.md`
- `docs/catalogs/FEATURE_USAGE_BY_MARKET.md`
- `docs/catalogs/FEATURE_OWNERSHIP_MATRIX.md`
- `src.data.model_data_field_catalog`
- `src.data.feature_registry`
- `src.market_intelligence.feature_packs`
- `src.services.streamlit_dashboard_data`
- `src.backtesting.backtest_schema`
- `src.data.validation`
- `src.providers`
- `src.connectors`

Detailed feature inventories remain in the catalogs and report layers.
This registry standardizes the cross-market schema and lifecycle that those inventories must follow.

## Feature Families Documented

| Feature family | Canonical role | Current state | Detailed inventory owner |
| --- | --- | --- | --- |
| Universal | Cross-market governing layer | Exists partially | This doc + `docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md` |
| Sports | Event-based sports features | Phase 5.1A contract-ready for the certified NFL historical dataset layer | `src.data.feature_registry`, `docs/contracts/NFL_FEATURE_STORE_CONTRACT.md`, and sport feature packs |
| Prediction Markets | Event / contract features | Scaffold only | `src.market_intelligence.feature_packs` and related catalogs |
| Options / 0DTE | Short-dated derivatives features | Scaffold only | `src.data.model_data_field_catalog` and related catalogs |
| Futures | Future extension | Documentation only | Roadmap and future catalogs |
| Crypto | Future extension | Documentation only | Roadmap and future catalogs |
| Macro | Future extension | Documentation only | Roadmap and future catalogs |

## Canonical Feature Registry Contract

Every feature entry in the repository should be able to report the following canonical fields:

- `Feature ID`
- `Feature Name`
- `Feature Family`
- `Market Family`
- `Feature Version`
- `Entity / Side Scope`
- `Dataset Grain Compatibility`
- `Purpose`
- `Description`
- `Required Inputs`
- `Dependencies`
- `Expected Output Type`
- `Value Type`
- `Unit`
- `Missingness Policy`
- `Source Dataset Field References`
- `Transformation Definition`
- `Transformation Version`
- `Cutoff Semantics`
- `Point-In-Time Constraints`
- `Expected Range / Allowed Values`
- `Owning Runtime Module`
- `Feature Owner`
- `Owning Market Profile`
- `Recommended Storage Owner`
- `Related Signals`
- `Related Targets`
- `Related Validation Metrics`
- `Related Engines`
- `Lifecycle Status`
- `Certification State`
- `Portability Classification`
- `Priority`

## Phase 5.1A Runtime Contract

The canonical runtime implementation for the first reusable feature layer is:

- `src.data.feature_registry`

The first active input dataset for this runtime contract is:

- `dataset.sports.nfl.historical_dataset`

Phase 5.1A established the reusable feature-definition and feature-snapshot grain rules.
Phase 5.1B now materializes feature rows from the certified historical dataset layer.
The certified historical dataset is the sole canonical input for the first feature layer.
Feature contracts must not reread or reselect predictor evidence from raw provider payloads or normalized source asset tables.

### Certified Dataset Row Grain

The certified Phase 5.0 dataset row grain remains:

- `dataset_id`
- `game_id`
- `market_type`
- `selection`
- `book`
- `decision_cutoff_time`

The corresponding row-level identities that later feature snapshots must inherit are:

- `dataset_row_id`
- `decision_context_id`

This preserves the three current fixture contexts as distinct rows:

- `moneyline / home / consensus`
- `spread / home / consensus`
- `total / over / consensus`

Totals remain event-scoped contexts and may intentionally have a blank `team_side`.

### Feature Snapshot Grain

The canonical feature-snapshot grain for the reusable feature layer is:

- one feature value
- for one certified `dataset_row_id`
- under one `decision_context_id`
- for one `feature_id`
- at one `feature_version`
- for one `entity_scope`
- at one `decision_cutoff_time`
- under one `transformation_version`

This prevents distinct market or team contexts from being collapsed or multiplied.
The current Phase 5.1B runtime persists those contexts as deterministic feature rows rather than treating the grain as contract-only metadata.

### Classification Rule

Every active feature definition must be classified as exactly one of:

- `direct`
- `deterministic derived`
- `deferred mathematical-engine output`

Phase 5.1A registers only dataset-supported direct and deterministic-derived features.
Mathematical outputs such as model probability, edge, expected value, Kelly sizing, and signals remain deferred.

### Point-In-Time Rule

All predictor features must inherit the certified game-level cutoff from Phase 5.0:

- `decision_cutoff_time = scheduled_kickoff_time - 5 minutes`

Feature definitions must preserve:

- `dataset_batch` identity
- `dataset_row_id`
- `decision_context_id`
- `scheduled_kickoff_time`
- `decision_cutoff_time`
- selected Phase 5.0 evidence timestamps
- source certification references
- source lineage references

Feature definitions must reject:

- post-cutoff odds
- post-cutoff injury revisions
- weather issued after the cutoff
- target-event live statistics
- target-event final statistics
- rolling statistics containing the target event
- final results in predictor namespaces
- raw-source rereads that bypass the certified dataset layer

## Feature Lifecycle

Every feature must mature through the same lifecycle.
No feature should jump directly from definition to production.

| State | Meaning |
| --- | --- |
| Defined | The feature has a canonical name and purpose. |
| Schema Ready | The expected fields, shapes, and timing constraints are documented. |
| Source Identified | At least one usable source or source family is known. |
| Connector Ready | A canonical acquisition or adapter path exists. |
| Historical Dataset Ready | Certified historical rows can supply the feature. |
| Math Ready | The calculation or derivation path is ready in the canonical runtime owner. |
| Signal Ready | The feature can be consumed as a reusable signal or registry asset. |
| Validated | The feature has evidence, lineage, and leakage checks. |
| Production Ready | The feature is usable in the current canonical workflow. |

The lifecycle tracking rule is:

Defined -> Schema Ready -> Source Identified -> Connector Ready -> Historical Dataset Ready -> Math Ready -> Signal Ready -> Validated -> Production Ready

## Registry Rules

1. Search for an existing canonical owner before adding a new feature.
2. Extend the existing owner if it already exists.
3. Create a new owner only when no canonical owner exists.
4. Keep storage, validation, lineage, and registry semantics shared across markets.
5. Do not create market-specific feature registries.
6. Keep result-only and post-event fields out of pregame feature snapshots.
7. Keep detailed feature entries in the supporting catalogs, not duplicated here.
8. Treat the certified historical dataset layer as the canonical feature-layer input once that layer exists.
9. Preserve `dataset_row_id`, `decision_context_id`, `decision_cutoff_time`, and selected evidence lineage when defining reusable feature snapshots.

## Naming Review

The [Master Research Engine Specification](./MASTER_RESEARCH_ENGINE_SPECIFICATION.md) now governs more than raw market inputs.
Its scope includes inputs, features, signals, targets, confidence metrics, validation metrics, connectors, engines, and research assets.
If the repository later needs an even broader top-level research asset registry, that should be handled as a separate future phase rather than another rename of this specification.

## Out Of Scope

This document does not:

- ingest data
- implement provider integrations
- implement mathematical formulas
- build feature pipelines
- build backtests
- build dashboards

It only defines the canonical registry schema and lifecycle that later phases must follow.
