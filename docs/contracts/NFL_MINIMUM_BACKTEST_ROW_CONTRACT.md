# NFL Minimum Backtest Row Contract

## Purpose

This document instantiates the reusable `Minimum Backtest Row Contract` for the NFL sports lane.

NFL is the first Sports Market Profile instance, so this contract makes the generic row contract concrete without creating a separate NFL architecture.

## NFL Backtest-Ready Definition

An NFL historical row is backtest-ready only when:

- it belongs to `sports:nfl`
- it represents exactly one game
- it has exactly one decision time
- it has a frozen odds / price snapshot at that decision time
- it has a frozen feature snapshot at that decision time
- it has a settled outcome attached only after the game is complete
- it has no unresolved leakage violation
- it has a documented lineage chain
- it has a documented validation status
- it satisfies the NFL sample floor

## NFL Baseline P0 Field Families

The NFL baseline uses 13 required P0 field families. All 13 must exist for the same game and the same decision time.

| # | Field family | What it covers |
| --- | --- | --- |
| 1 | Market profile identity | `sports:nfl` and the Sports profile family |
| 2 | Game identity | `season`, `week`, `game_id`, teams, and event identifiers |
| 3 | Market identity | `market_type`, `selection`, and the market-side label |
| 4 | Provider identity | `provider`, `source`, and book or exchange metadata |
| 5 | Decision timing | `decision_time` and the cutoff that freezes the row |
| 6 | Odds snapshot | `odds_snapshot_time`, line, odds, and price type |
| 7 | Feature snapshot | `feature_snapshot_time`, `feature_pack_version`, and `dataset_version` |
| 8 | Schedule context | kickoff / start time and schedule alignment |
| 9 | Outcome attachment | final result, settlement status, and result timestamp |
| 10 | Lineage chain | source dataset IDs, snapshot IDs, and transformation IDs |
| 11 | Validation state | completeness, point-in-time, leakage, and quality status |
| 12 | Exclusion / no-trade state | why the row was skipped or excluded, if applicable |
| 13 | Historical sample coverage | enough usable rows across a valid historical window |

## NFL Sample Floor

The minimum readiness floor for NFL baseline work is:

- at least 2 full regular seasons, or
- at least 400 resolved decision rows,
- whichever is greater

This threshold is the minimum bar for the first reusable NFL backtest slice.

## NFL Decision-Time Rules

The NFL row must satisfy all of the following:

- every required field is aligned to the same game
- every pregame feature is known at or before `decision_time`
- weather must use forecast timing, not actual game-time conditions
- injuries must use report timing, not postgame updates
- depth chart data must use snapshot timing, not later roster revisions
- closing line data may be used for CLV or post-event evaluation, not as a pregame feature
- outcome fields must be attached after event completion only

## NFL Readiness States

| State | Meaning |
| --- | --- |
| `BACKTEST_ELIGIBLE` | The NFL row is complete, time-safe, and can be used in a baseline backtest. |
| `NO_TRADE` | The row is complete enough to evaluate but should not be wagered or counted as a live decision. |
| `EXCLUDED` | The row is incomplete, unsafe, or missing a required field family. |
| `NEEDS_REVIEW` | The row is ambiguous and needs a manual or rule-based decision. |

## NFL Minimum Readiness Rule

The NFL baseline is backtest-ready only when:

- 13/13 required P0 field families exist
- the fields exist for the same game
- the fields align to the same `decision_time`
- all features are known at or before `decision_time`
- outcomes are attached only after event completion
- no unresolved leakage violations remain
- the sample floor has been met
- every excluded row has a clear exclusion reason

## NFL Streamlit Readiness

Future NFL dashboard readiness views should show:

- required fields complete
- usable rows
- excluded rows
- exclusion reasons
- seasons covered
- market types covered
- leakage warnings
- validation status
- readiness percentage
- backtest-ready yes / no

## NFL Worldview Compatibility

The future Worldview layer should be able to ask:

- is NFL backtest-ready?
- which NFL field families are missing?
- which NFL features are blocked by leakage?
- how many valid NFL rows exist?
- what evidence package can be returned for NFL?

## Relationship to the Generic Contract

This document does not redefine the reusable contract.
It instantiates the generic contract for the NFL lane and gives the first market-specific baseline numbers.

Any future sports market should follow the same pattern:

- resolve the shared profile contract first
- then apply sport-specific field families
- then apply the market-family sample floor
