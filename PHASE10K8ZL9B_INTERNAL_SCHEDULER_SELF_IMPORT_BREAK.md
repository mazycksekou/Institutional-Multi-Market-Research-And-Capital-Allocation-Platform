# PHASE 10K8ZL9B - Internal Scheduler Self-Import Break

This phase removes direct `automation_scheduler` imports from the 13 known
internal self-importing scheduler files without deleting scheduler code.

## Outcome

- 13 targeted scheduler files were redirected to canonical `src.*` modules.
- No scheduler files were deleted.
- The scheduler package still exists.
- The next blocker is the bridge/support layer plus test import redirection.

## Canonical redirection targets

- `src.market_intelligence.feature_packs`
- `src.research.feature_control`
- `src.research.history`
- `src.data.field_catalog`
- `src.data.historical_sources`
- `src.data.historical_odds`
- `src.data.line_movement`
- `src.data.source_event_links`
- `src.backtesting.dataset_builder`
- `src.backtesting.strategy_profiles`
- `src.backtesting.engine`
- `src.backtesting.historical_bridge`

