# Sports Market Profile

The Sports Market Profile is the reusable contract family for all sports markets in this repository.

## Scope

This family covers sports event and player markets that share the same general structure:

- league
- season
- event identifiers
- team identifiers
- player identifiers
- market identifiers
- odds snapshots
- results
- feature groups
- validation rules
- leakage rules
- backtest requirements

## Canonical fields

The Sports profile family treats the following as core contract fields:

- `league`
- `season`
- `event_id`
- `team_id`
- `player_id`
- `position_group`
- `market_id`
- `odds_snapshot`
- `result`
- `decision_time`
- `snapshot_time`
- `feature_group`

## Feature groups

The Sports profile family is expected to support both atomic and composite feature groups.

Examples:

- Atomic: league fields, season fields, event identifiers, team fields, player fields, position groups
- Composite: odds movement, injury impact, weather impact, rest/travel, market context

## Validation and leakage

Sports profiles must:

- preserve point-in-time safety
- avoid post-event leakage into pregame features
- freeze snapshots at decision time
- reject result fields as feature inputs

## NFL relationship

NFL is the first Sports profile instance.

The same family should support future sports without changing the framework:

- NFL extends the Sports profile contract
- future sports add their own sport-specific fields and feature groups
- no separate architecture should be created for each sport
