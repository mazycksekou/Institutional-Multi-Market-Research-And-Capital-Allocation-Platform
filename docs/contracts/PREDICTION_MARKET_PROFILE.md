# Prediction Market Profile

The Prediction Market Profile is the reusable contract family for event-based prediction markets.

## Scope

This family is designed for markets that expose:

- event IDs
- contract IDs
- market IDs
- settlement rules
- bid/ask data
- liquidity
- order book snapshots
- point-in-time timestamps
- backtest support

## Canonical fields

The reusable prediction-market contract includes:

- `event_id`
- `contract_id`
- `market_id`
- `settlement_rule`
- `liquidity`
- `bid`
- `ask`
- `order_book_snapshot`
- `decision_time`
- `snapshot_time`

## Validation and leakage

Prediction market profiles must:

- preserve snapshot timestamps
- freeze book state at the time of decision
- keep settlement truth out of pre-settlement features
- support settlement-aware replay

## Intended use

This profile is used as the canonical pattern for future prediction-market data, storage, feature, and backtest contracts.

It is not a provider implementation.
