# PHASE 10K8ZHM Data / Backtesting Checkpoint

## Summary

`src.data` and `src.backtesting` now exist as canonical foundations. The repo
still preserves the legacy scheduler/backtest stack, and no live data or
execution behavior has been activated.

## Current Status

### Data foundation status

- created
- local-only
- registry-driven

### Backtesting foundation status

- created
- local-only
- planning-only

### Legacy mapping status

- documented
- no legacy deletion
- automation_scheduler still preserved

### Deferred domains

- live data activation: not started
- no live data activation
- broker execution: not started
- no broker execution
- AI/LLM deferred
- analytics next
- research next

## What This Phase Does Not Change

- no live calls
- no credential reads at import time
- no brokerage/live execution
- no behavior-changing migrations
- no legacy deletions

## Next Recommended Path

Move toward `src.analytics` and `src.research` ownership after the data and
backtesting foundations are validated.
