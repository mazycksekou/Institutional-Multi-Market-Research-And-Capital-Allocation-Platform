# Options / 0DTE Market Profile

The Options / 0DTE Market Profile is the reusable contract family for short-dated options market analysis.

## Scope

This family is designed for options markets that need to represent:

- symbol
- expiration
- strike
- option type
- Greeks
- implied volatility
- open interest
- volume
- dealer positioning
- point-in-time timestamps

## Canonical fields

The reusable options profile includes:

- `symbol`
- `expiration`
- `strike`
- `option_type`
- `greeks`
- `implied_volatility`
- `open_interest`
- `volume`
- `dealer_positioning`
- `decision_time`
- `snapshot_time`

## Validation and leakage

Options profiles must:

- preserve option-chain snapshot timing
- avoid using intraday truth after the fact as if it were pre-event data
- keep expiration explicit
- support expiry-aware replay and backtesting

## Intended use

This profile becomes the canonical options foundation for later options and 0DTE work.

It is not a provider implementation and does not expose proprietary trading logic.
