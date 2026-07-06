# NFL Provider / Source Mapping

This document maps the required NFL baseline features to the source categories that can satisfy them.
It does not implement providers. It only records the source strategy.

## Source Categories

- LOCAL_CSV
- LOCAL_JSON
- LOCAL_PARQUET
- SQLITE
- DUCKDB
- FREE_API
- OPEN_DATA
- MANUAL_EXPORT
- COMPUTED
- UNKNOWN
- PAID_OR_DEFERRED

## Mapping

| Feature family | Preferred source categories | Notes |
| --- | --- | --- |
| schedule / results / game metadata | OPEN_DATA, LOCAL_CSV, LOCAL_JSON, SQLITE, DUCKDB | Foundation data; should be reproducible from local storage. |
| open odds / pregame market snapshots | FREE_API, LOCAL_CSV, LOCAL_JSON, OPEN_DATA | Needs explicit snapshot timestamps. |
| weather forecast snapshots | FREE_API, OPEN_DATA, LOCAL_JSON | Must distinguish forecast time from actual weather. |
| injury / availability snapshots | OPEN_DATA, LOCAL_JSON, MANUAL_EXPORT, PAID_OR_DEFERRED | Only safe when time-stamped before the decision point. |
| depth chart snapshots | OPEN_DATA, LOCAL_CSV, LOCAL_JSON, MANUAL_EXPORT, PAID_OR_DEFERRED | Late changes must not leak into pregame features. |
| offensive / defensive efficiency | COMPUTED, OPEN_DATA, LOCAL_PARQUET, SQLITE, DUCKDB | Derived from prior-game history only. |
| pace / play volume | COMPUTED, OPEN_DATA, LOCAL_PARQUET, SQLITE, DUCKDB | Best built from historical play-by-play or game results. |
| roster continuity | COMPUTED, LOCAL_CSV, LOCAL_JSON, SQLITE | Derived from prior roster and game participation history. |
| coaching continuity | COMPUTED, OPEN_DATA, LOCAL_CSV, LOCAL_JSON | Derived from coaching records and historical staff continuity. |
| travel fatigue / rest advantage | COMPUTED, OPEN_DATA, LOCAL_CSV, LOCAL_JSON | Derived from schedule and venue history. |
| offensive line score | COMPUTED, OPEN_DATA, LOCAL_PARQUET, SQLITE, DUCKDB | Needs stable historical inputs. |
| defensive line pressure score | COMPUTED, OPEN_DATA, LOCAL_PARQUET, SQLITE, DUCKDB | Needs stable historical inputs. |
| red zone / third down efficiency | COMPUTED, OPEN_DATA, LOCAL_PARQUET, SQLITE, DUCKDB | Historical only. |
| special teams efficiency | COMPUTED, OPEN_DATA, LOCAL_PARQUET, SQLITE, DUCKDB | Historical only. |
| official crew tendency | OPEN_DATA, FREE_API, LOCAL_CSV | Acceptable if the assignment is time-stamped. |
| draft capital / combine context | OPEN_DATA, LOCAL_CSV, MANUAL_EXPORT | Optional context, not required for the baseline slice. |
| route share / tracking | PAID_OR_DEFERRED, UNKNOWN | Explicitly deferred. |
| player props inputs | PAID_OR_DEFERRED, UNKNOWN | Defer until the baseline team/game slice is stable. |

## Baseline Source Strategy

The first NFL slice should prefer:

1. open data
2. local files
3. computed features from validated historical rows
4. free APIs where they are stable and timestamped

Paid or deferred sources should remain optional until the repository can prove they are necessary, reproducible, and worth the maintenance cost.

