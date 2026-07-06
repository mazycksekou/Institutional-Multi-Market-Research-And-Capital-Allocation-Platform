# NFL Phase 4.3 Implementation Plan

This plan is the next step after the Phase 4.2 research blueprint is approved.
It is intentionally narrow and architecture-first.

## Recommended Phase 4.3 Slice

1. Canonical team / game storage
2. Odds snapshot storage with timestamps
3. Weather / injury / depth-chart snapshot storage
4. One reproducible NFL feature snapshot builder
5. One baseline backtest harness for spread / moneyline / totals
6. One Streamlit evidence view that shows readiness and model status

## Build Order

### Step 1: Storage first

Create or promote the smallest stable tables needed for the baseline slice.

### Step 2: Snapshot timing

Freeze decision-time inputs and record lineage for every row.

### Step 3: Baseline feature pack

Build only the P0 features required for the first model attempt.

### Step 4: Backtest harness

Run chronological, point-in-time-safe evaluation only.

### Step 5: Dashboard evidence

Show readiness, leakage status, and baseline results in one place.

## Do Not Start Yet

- player props
- live execution
- paid / live / charting-heavy providers
- tracking data
- broad feature expansion beyond the baseline slice

## Success Criteria

The implementation phase should prove that the repository can:

- store NFL evidence reproducibly,
- build a frozen feature snapshot,
- run a deterministic backtest,
- and explain the result to a reviewer.

