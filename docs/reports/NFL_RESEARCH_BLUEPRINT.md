# NFL Research Blueprint

This blueprint translates the Phase 4.1 NFL discovery work into the first reusable NFL research slice.
It is practical, not theoretical.

## Executive Summary

The first NFL slice should be a point-in-time safe team/game foundation that supports spread, moneyline, and totals modeling.
The blueprint should prioritize reusable open-data and local-source paths first, then layer in validated context signals.

## 1. Smallest Dataset Needed

The minimum useful dataset is:

- game identity and schedule context
- settled result rows
- pregame odds snapshots
- pregame weather snapshots
- pregame injury / availability snapshots
- pregame depth chart snapshots
- recent team efficiency context
- roster / coaching continuity context

This is enough to support a first reproducible model attempt without jumping to player props or live trading.

## 2. Feature Priorities

See `docs/reports/NFL_FEATURE_PRIORITY_MATRIX.md` for the full matrix.

For the first slice:

- **P0** features are the minimum viable baseline inputs
- **P1** features improve model quality and stability
- **P2** features are useful after baseline validation works
- **P3** features are future extensions
- **DEFER** features stay out of the first slice

## 3. Point-in-Time Safety

The blueprint only accepts features with known timing.
If a field cannot be timestamped before the decision point, it is either deferred or used only as a result/evaluation field.

### Safe by default

- schedule and kickoff data
- pregame odds snapshots
- weather forecasts taken before kickoff
- injuries and depth charts captured before kickoff
- team historical context cut off before the decision time

### Not safe for pregame features

- final score
- closing line after the decision point
- postgame injury outcomes
- actual weather after kickoff
- postgame player stats

## 4. Provider / Source Strategy

The first slice should prefer:

- local files
- open data
- free public APIs
- computed features built from validated source rows

Paid or deferred sources should stay out of the baseline unless the repository later proves they are both necessary and reproducible.

## 5. Storage and Join Strategy

The blueprint should center on:

- game-level fact tables
- team schedule tables
- odds snapshot tables
- weather snapshot tables
- injury / availability snapshot tables
- feature snapshot tables
- backtest rows and backtest result tables

Every join must be keyed by a reproducible game identifier plus the relevant snapshot timestamp or version identifier.

## 6. Backtest Gate

The first backtest should not be judged on vibes.
It should be judged on reproducible evidence:

- enough games to avoid accidental noise
- chronological splits only
- point-in-time frozen inputs
- calibrated probability outputs
- net return after costs / vig assumptions
- explicit no-trade rules when the data is incomplete

## 7. Dashboard / Reporting Needs

The first dashboard slice should make the system understandable, not flashy.
It should show:

- dataset readiness
- provider readiness
- feature readiness
- leakage warnings
- backtest summary
- CLV / ROI summary
- calibration chart
- model comparison
- no-trade reasons
- Worldview experiment readiness

## 8. Worldview Compatibility

The future Worldview Intelligence Layer should be able to ask:

- what hypothesis are we testing?
- which point-in-time safe features are allowed?
- what data snapshot supports the experiment?
- what evidence package came back?

The repository should answer those questions with a reproducible experiment record, not a narrative.

## 9. Next Implementation Step

The smallest reusable NFL implementation slice is:

1. canonical team/game data storage
2. odds snapshot storage
3. timestamped weather / injury / availability snapshots
4. one reproducible NFL feature snapshot builder
5. one baseline backtest harness for spread / moneyline / totals
6. one Streamlit view that shows readiness and evidence

That is the right Phase 4.3 target after this blueprint is agreed.

