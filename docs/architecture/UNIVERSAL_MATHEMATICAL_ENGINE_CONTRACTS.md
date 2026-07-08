# Universal Mathematical Engine Contracts

This document defines the canonical contract layer for reusable mathematical engines across every supported market family in the repository.

It sits above the [Master Market Input Specification](./MASTER_MARKET_INPUT_SPECIFICATION.md) and the [Universal Feature Registry](./UNIVERSAL_FEATURE_REGISTRY.md), and below the runtime owners in `src.core`.
It does not implement formulas, data ingestion, feature engineering, signals, targets, models, or backtests.

## Canonical Owners Reused

- `docs/architecture/MASTER_MARKET_INPUT_SPECIFICATION.md`
- `docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md`
- `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`
- `src.core`
- `src.data.validation`
- `src.research`
- `src.analytics`
- `src.backtesting`
- `src.market_intelligence`

These owners already cover the math primitives, reusable validation, research workflow, analytics summaries, backtest consumption, and domain-facing orchestration.
This document standardizes the cross-market contract shape that those owners must obey.

## Research Asset Framing

Mathematical engines are governed research assets, not ad hoc calculations.

Each engine must have:

- one canonical owner
- one dependency chain
- one lifecycle
- one validation path
- one lineage chain

No engine may reference a feature that is not represented in the Universal Feature Registry.
No engine should be defined without a known output shape and lifecycle state.

## Canonical Engine Contract Fields

Every mathematical engine entry should be able to report the following canonical fields:

- `Engine ID`
- `Engine Name`
- `Purpose`
- `Description`
- `Supported Markets`
- `Required Input Feature IDs`
- `Produced Output Feature IDs`
- `Input Data Types`
- `Output Data Types`
- `Units`
- `Dependencies`
- `Numerical Stability Requirements`
- `Point-in-Time Requirements`
- `Validation Rules`
- `Error Conditions`
- `Versioning Rules`
- `Lineage Requirements`
- `Owning Runtime Module`
- `Owning Validation Module`
- `Priority`
- `Lifecycle Status`

## Initial Engine Families

### Universal Families

| Family | Example engines | Supported markets | Canonical role | Lifecycle status |
| --- | --- | --- | --- | --- |
| Probability | Probability, Implied Probability | Cross-market | Base probability transformation layer | Contract Ready |
| No-Vig Pricing | No-Vig Probability | Cross-market | Vig removal and fair-probability normalization | Contract Ready |
| Expected Value | Expected Value | Cross-market | Value estimation from odds and probability inputs | Contract Ready |
| Edge | Edge | Cross-market | Difference between implied and model-derived probability | Contract Ready |
| Kelly | Kelly | Cross-market | Fractional and capped bankroll sizing | Contract Ready |
| Closing Line Value | Closing Line Value | Cross-market | Outcome-aware price quality measurement | Contract Ready |
| Calibration | Calibration | Cross-market | Probability and market calibration measurement | Contract Ready |
| Position Sizing | Position Sizing | Cross-market | Stake and exposure decision support | Contract Ready |
| Confidence | Confidence | Cross-market | Confidence scoring and decision gating | Contract Ready |
| Risk | Risk | Cross-market | Exposure, drawdown, and risk-control support | Contract Ready |
| Target | Target | Cross-market | Target derivation for later experiment and model stages | Contract Ready |
| Validation | Validation | Cross-market | Validation-result scoring and readiness gating | Contract Ready |
| Data Quality | Data Quality | Cross-market | Source and row-quality assessment | Contract Ready |

### Sports Families

| Family | Example engines | Supported markets | Canonical role | Lifecycle status |
| --- | --- | --- | --- | --- |
| Sports market movement | Reverse Line Movement, Steam Detection, Sharp/Public Divergence, Consensus Line, Market Movement | Sports | Sports-specific line and market behavior analysis | Contract Ready |

### Options / 0DTE Families

| Family | Example engines | Supported markets | Canonical role | Lifecycle status |
| --- | --- | --- | --- | --- |
| Options math | Greeks, Black-Scholes, GEX, Vanna, Charm, Volatility Surface, Gamma Flip, Call Wall, Put Wall, Expected Move | Options / 0DTE | Derivatives math and surface analysis | Contract Ready |

### Prediction Market Families

| Family | Example engines | Supported markets | Canonical role | Lifecycle status |
| --- | --- | --- | --- | --- |
| Prediction market structure | Probability Walls, Liquidity, Order Book, Holder Concentration, Market Efficiency | Prediction Markets | Contract-only market microstructure analysis | Contract Ready |

## Dependency Rule

No mathematical engine may reference a feature that is not represented in the Universal Feature Registry.

That means:

1. engine inputs must be registered features
2. engine outputs must be registered features
3. engine dependencies must be explicit
4. engine lineage must be traceable back to certified datasets
5. engine validation must reuse the shared validation layer

This rule keeps formula ownership separate from feature ownership and prevents engines from quietly inventing new data dependencies.

## Research Asset Lifecycle

Every mathematical engine must support the same lifecycle:

Defined -> Contract Ready -> Schema Ready -> Inputs Available -> Historical Dataset Ready -> Math Implemented -> Validated -> Backtested -> Production Ready

Lifecycle meaning:

- Defined: the engine has a canonical name and purpose
- Contract Ready: the contract fields, inputs, outputs, and owners are documented
- Schema Ready: the expected field shape and types are documented
- Inputs Available: the required feature IDs are known and governable
- Historical Dataset Ready: certified historical inputs exist for the engine
- Math Implemented: a runtime implementation exists in the canonical owner
- Validated: the implementation and outputs satisfy validation rules
- Backtested: the engine has been evaluated on certified historical rows
- Production Ready: the engine can be consumed by the current canonical workflow

## Validation and Stability Rules

Every engine contract must define:

- numerical stability requirements
- point-in-time requirements
- validation rules
- error conditions
- versioning rules
- lineage requirements

The repository should prefer deterministic math, explicit versioning, and stable output shapes over clever but opaque shortcuts.

## Future Registry Consideration

The repository may eventually benefit from a top-level Research Asset Registry that unifies:

- datasets
- features
- mathematical engines
- signals
- targets
- connectors
- models
- experiments
- evidence

If the repository keeps broadening its asset catalog, that registry should be introduced later as a new canonical owner rather than as another parallel inventory.
Do not implement that registry in this phase.

## Out Of Scope

This document does not:

- implement formulas
- ingest data
- implement provider integrations
- implement feature engineering
- implement signals
- implement targets
- implement models
- implement backtests

It only defines the reusable mathematical engine contract layer that later phases must follow.
