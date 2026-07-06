# NFL Baseline Model Scope

This document defines the smallest practical NFL model scope for the first reusable slice.
The starting point is the open-data team/game foundation, not player props, live betting, or paid charting.

## Recommended Baseline Markets

| Market | Include now? | Why |
| --- | --- | --- |
| Spread | Yes | Best first market for a team/game model with clear decision-time inputs. |
| Moneyline | Yes | Useful for sanity checks, calibration, and model comparison. |
| Totals | Yes | Reuses many of the same timing, weather, and pace inputs. |
| Player props | No | Defer until the source layer and player-level timing are materially stronger. |

## Required Inputs for the Baseline Slice

### Raw fields

- game identity
- season / week / game type
- home team / away team
- kickoff timestamp
- venue / location
- score result
- market snapshot timestamp
- odds at decision time
- weather forecast snapshot
- injury / availability snapshot
- depth chart snapshot
- team efficiency history

### Derived features

- rest advantage
- travel fatigue
- pace trend
- scoring profile trend
- defensive efficiency trend
- offensive efficiency trend
- roster continuity
- coaching continuity
- injury-adjusted availability
- weather impact score

### Required timestamps

- decision timestamp
- odds snapshot timestamp
- weather forecast timestamp
- injury snapshot timestamp
- depth chart snapshot timestamp
- game kickoff timestamp
- game result timestamp

### Required metadata

- dataset version
- schema version
- source name
- provider type
- lineage identifier
- quality score

## Why this scope works

- It stays point-in-time safe.
- It uses the open-data and local-source lanes first.
- It supports reproducible backtesting and calibration.
- It is small enough to ship, but large enough to prove the architecture.

## Explicitly Deferred

- player tracking
- live betting
- props-specific modeling
- paid provider dependencies
- non-reproducible manual analysis

