# NFL Backtest Row Exclusion Rules

## Purpose

These rules state when an NFL row must be skipped, excluded, or reviewed before backtesting.

## States

| State | Meaning |
| --- | --- |
| `BACKTEST_ELIGIBLE` | The row is complete, aligned, and usable. |
| `NO_TRADE` | The row is valid but the strategy should skip it. |
| `EXCLUDED` | The row is not usable because a required field or timestamp is missing or unsafe. |
| `NEEDS_REVIEW` | The row is ambiguous and needs human or rule-based review. |

## Common exclusion reasons

| Reason | Typical state |
| --- | --- |
| Missing odds snapshot | `EXCLUDED` |
| Missing result | `EXCLUDED` |
| Missing decision time | `EXCLUDED` |
| Feature timestamp after decision time | `EXCLUDED` |
| Weather actual used instead of forecast | `EXCLUDED` |
| Injury update after decision time | `EXCLUDED` |
| Closing line used as a pregame feature | `EXCLUDED` |
| Missing lineage | `EXCLUDED` |
| Invalid market profile | `EXCLUDED` |
| Unsupported market type | `EXCLUDED` |
| Low source quality | `NEEDS_REVIEW` or `EXCLUDED` depending on severity |
| Model under threshold | `NO_TRADE` |
| Evaluation window too small | `NO_TRADE` |
| Chronology is valid but edge is weak | `NO_TRADE` |

## Exclusion rule

A row is excluded when:

- a required field family is missing
- a required timestamp is unsafe
- leakage cannot be ruled out
- lineage cannot be reconstructed
- the market is not supported by the current contract

## No-trade rule

A row is a no-trade when:

- the row is technically valid
- the strategy or gate says not to wager
- the reason is explicit and recorded

## Review rule

Use `NEEDS_REVIEW` when:

- the timing is ambiguous
- the source quality is uncertain
- the row might be valid, but the decision cannot be made mechanically yet

## Minimum audit note

Every skipped row should have a machine-readable reason so the repository can answer why the row was not used.
