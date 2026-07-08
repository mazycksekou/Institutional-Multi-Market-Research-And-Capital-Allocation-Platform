# Market Profile Framework

The Market Profile Framework is the reusable contract layer that defines how this repository describes a market before any provider, ingestion, feature, backtesting, or dashboard work happens.

It lives inside the existing canonical architecture:

- `src/data/market_profile_contracts.py`
- `src/data/market_profile_registry.py`
- `src/market_intelligence/market_profiles.py`

## Purpose

The framework gives every market family a stable profile that answers the same questions:

- What identifies the market?
- Which timestamps are required?
- Which fields are canonical?
- Which feature groups are atomic or composite?
- Which validation and leakage rules apply?
- Which storage, feature store, backtest, research, Streamlit, paper trading, and live-execution gates exist?
- What permissions does the future Worldview layer have?

This keeps market expansion inside one canonical shape instead of creating one-off schemas per market.

## Supported profile families

The framework currently supports three reusable families:

| Profile family | Purpose | Notes |
| --- | --- | --- |
| Sports | Sports markets across leagues and event types | NFL is the first instance, not a separate architecture |
| Prediction markets | Event/contract/market based prediction instruments | Designed for event IDs, contract IDs, settlement rules, and order book snapshots |
| Options / 0DTE | Options market profiles focused on short-dated contracts | Designed for chain snapshots, Greeks, IV, and dealer positioning |

## Canonical ownership

The framework is intentionally split into three layers:

1. Contract definition in `src/data/market_profile_contracts.py`
2. Registry management in `src/data/market_profile_registry.py`
3. Canonical market catalog in `src/market_intelligence/market_profiles.py`

That separation keeps validation reusable while keeping market semantics in market-intelligence space.

## NFL compatibility

NFL belongs inside the Sports profile family.

That means:

- NFL reuses the Sports contract shape
- NFL extends sports-specific field groups rather than inventing a new market architecture
- Future sports should reuse the same framework and only add sport-specific extensions

NFL is the first sports-profile instance because it is the first market slice being planned in this repository, but the framework itself is not NFL-specific.

The next layers above this framework are the [Master Research Engine Specification](./MASTER_RESEARCH_ENGINE_SPECIFICATION.md) and the [Universal Feature Registry](./UNIVERSAL_FEATURE_REGISTRY.md), which turn reusable profiles into the governed inventory of inputs, features, metrics, signals, targets, confidence values, validation rules, connectors, and engines.

## Required contract dimensions

Each profile declares:

- `profile_id`
- `profile_family`
- canonical identifiers
- required timestamps
- canonical fields
- atomic feature groups
- composite feature groups
- validation rules
- leakage rules
- storage requirements
- feature store requirements
- backtest requirements
- Streamlit requirements
- research requirements
- Worldview permissions
- paper-trading requirements
- live-execution gates

## Design goals

The framework is designed to be:

- canonical
- reusable
- versionable
- point-in-time aware
- leakage conscious
- storage aware
- backtest aware
- research aware
- Worldview compatible
- easy to extend without duplicate ownership

## Out of scope

This framework does not:

- ingest data
- fetch provider data
- build feature pipelines
- build backtests
- build dashboards
- train models
- execute trades

It only establishes the reusable market contract layer those systems can plug into later.
