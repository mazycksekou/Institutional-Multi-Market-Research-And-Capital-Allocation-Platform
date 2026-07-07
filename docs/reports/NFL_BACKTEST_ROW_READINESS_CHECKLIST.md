# NFL Backtest Row Readiness Checklist

## Purpose

This checklist proves whether an NFL decision row is ready for backtesting.

The row is only backtest-ready when the checklist is complete and the row is aligned to the same game and the same decision time.

## Checklist

### Required field families

- [ ] `sports:nfl` profile resolved
- [ ] season / week / `game_id` present
- [ ] market type / selection present
- [ ] provider / source / book metadata present
- [ ] `decision_time` present
- [ ] odds snapshot frozen at decision time
- [ ] feature snapshot frozen at decision time
- [ ] schedule / kickoff timing present
- [ ] outcome attached after event completion
- [ ] lineage chain present
- [ ] validation status present
- [ ] exclusion / no-trade reason documented when applicable
- [ ] historical sample floor met

### Timing checks

- [ ] all pregame inputs are at or before `decision_time`
- [ ] no feature timestamp occurs after `decision_time`
- [ ] weather uses forecast timing, not actual game weather
- [ ] injuries use report timing, not later updates
- [ ] closing line is not used as a pregame feature
- [ ] result timestamp occurs after event completion

### Quality checks

- [ ] row completeness status is known
- [ ] point-in-time status is known
- [ ] leakage status is known
- [ ] source quality score is known
- [ ] validation errors are empty or explained

## Minimum Readiness Bar

The minimum readiness bar is:

- 13 / 13 required P0 field families present
- same game / same event
- same decision time
- no unresolved leakage violation
- minimum sample floor satisfied

## Outcome

- backtest-ready yes / no
- usable rows count
- excluded rows count
- no-trade rows count
