# PHASE10K8ZGJ Odds Legacy Live-Method Retirement

## Executive Summary
`10K8ZGJ` retires live-method bodies in the legacy odds/sportsbook surface and converts them into disabled compatibility shells. The canonical odds connector boundary already lives under `src.connectors.odds_data`, and the legacy modules now delegate status/configuration metadata there instead of owning live behavior.

This phase keeps import compatibility intact and preserves the scheduler/utility shapes that downstream code still expects.

## Current HEAD
`95dc6fa35008d7c652140883f050ac3aade73cf5`

## Purpose
Move legacy odds modules from live ownership to disabled compatibility ownership without deleting anything yet.

## Scope
Modules updated in this phase:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`

## Non-Goals
- No files deleted
- No files moved
- No source-function migration
- No public functions removed
- behavior unchanged for import compatibility and scheduler wiring outside retiring live-method bodies
- No live API calls
- No credential reads at import time

## Relationship to 10K8ZGI
`10K8ZGI` redirected odds runtime consumers to the canonical connector metadata. `10K8ZGJ` takes the next step and removes live execution ownership from the legacy odds modules themselves.

## Retired Live Methods
- `sharp_client.get_sharp_active_events(...)`
- `sharp_client.get_sharp_event_odds(...)`
- `betting_providers.sharp_api.SharpApiAdapter.get_supported_sports(...)`
- `betting_providers.sharp_api.SharpApiAdapter.get_active_events(...)`
- `betting_providers.sharp_api.SharpApiAdapter.get_event_odds(...)`
- `betting_providers.sharp_api.SharpApiAdapter.get_first_event_odds(...)`
- `betting_providers.the_odds_api.TheOddsApiAdapter.get_supported_sports(...)`
- `betting_providers.the_odds_api.TheOddsApiAdapter.get_odds_events(...)`
- `betting_providers.the_odds_api.TheOddsApiAdapter.get_active_events(...)`
- `betting_providers.the_odds_api.TheOddsApiAdapter.get_event_odds(...)`
- `betting_providers.the_odds_api.TheOddsApiAdapter.get_first_event_odds(...)`
- `betting_providers.sportsgameodds.SportsGameOddsAdapter.get_active_events(...)`
- `automation_scheduler.sharp_sportsbook_adapter.SharpSportsbookAdapter.fetch_events(...)`
- `automation_scheduler.sharp_sportsbook_adapter.SharpSportsbookAdapter.fetch_odds(...)`
- `automation_scheduler.sharp_sportsbook_adapter.SharpSportsbookAdapter.fetch_player_props(...)`
- `automation_scheduler.sharp_sportsbook_adapter.SharpSportsbookAdapter.fetch_sports(...)`

## Compatibility Shell Behavior
- `providers.sharp_provider.enrich_with_sharp(...)` now returns disabled connector metadata only
- `automation_scheduler.sharp_sportsbook_adapter.fetch_snapshot(...)` now returns a disabled snapshot placeholder
- `automation_scheduler.sportsbook_odds_provider` continues to summarize/write snapshots without live calls
- Legacy module names and import paths remain stable

## Required Statement
Legacy odds modules are converted toward disabled compatibility shells in this phase. This phase does not authorize live API calls, credential reads, bet execution, route rewrites, connector activation, or deletion.

## Delete Readiness
None of the legacy odds live-method shells are deleted in this phase. They remain importable so downstream callers can be redirected and proven safe before any removal batch.

## Remaining Blockers
- Downstream import scans still need full proof that no runtime caller requires the legacy live-method bodies
- Legacy odds tests that exercised live behavior must be updated to the disabled shell contract
- Scheduler and screenshot flows still depend on the compatibility shell import paths

## Next Phase Recommendation
Proceed to a delete-proof phase for the odds legacy compatibility shells after the redirected consumers and updated tests are fully green.
