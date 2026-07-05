# Phase 10H10 – Sport Data Explorer + Field Coverage Matrix

## Summary

Added a **Data Explorer** page to the Streamlit operator dashboard that turns the
dashboard from a developer control room into an operator cockpit.  The page shows
what historical odds data is available, which fields are present or missing, and
whether a sport/market combination is ready for projection.

## What was implemented

### New page in the dashboard menu

- **Data Explorer** – accessible from the sidebar radio menu.

### New helper functions in `streamlit_dashboard_data.py`

- `classify_market_family(market, selection)` – returns one of:
  `moneyline_or_1x2`, `spread_or_runline`, `total`, `team_total`,
  `player_prop`, `unknown`.
- `get_required_field_groups_for_market(market_family)` – returns a dict of
  field groups (core_event, line_core, line_movement, settlement, etc.) required
  for the market family.
- `calculate_field_coverage(rows, required_groups)` – for each field returns
  present count, missing count, coverage percent, and status (`good`, `partial`,
  `missing`).
- `build_market_readiness_report(rows)` – returns a report with flags for
  projection_ready, settlement_ready, line_movement_ready, player_prop_ready,
  team_stats_ready, plus critical missing fields and human‑readable reason.
- `get_sqlite_data_explorer_snapshot_for_dashboard(...)` – connects to the
  SQLite store, applies filters, computes coverage and readiness, and returns
  a JSON‑serializable snapshot.

### What the Data Explorer page displays

1. **Summary metrics** – total rows, sports, leagues, markets, and ready flags.
2. **Available Markets / Lines** – deduplicated table of sport, league, market,
   market family, source key.
3. **Field Coverage** – table of each field with presence/missing counts and status.
4. **Missing Critical Fields** – grouped list of fields that are entirely absent.
5. **Operator Interpretation** – simple text hints (e.g. “ROI may be weak …”).
6. **Sample rows** – Arrow‑safe display of up to 20 rows.
7. **Full snapshot JSON** – expandable raw result.

## What was fixed

- The dashboard title no longer contains “??”.

## How it helps

- Prevents bad projections by showing missing data **before** running a backtest.
- Helps operators decide which sports/leagues/markets have enough data for
  meaningful paper testing.
- Makes field coverage visible so developers know which importers or mappings
  need work.

## Next phase

- **Phase 10H11** – Line Movement Schema + Historical Odds Snapshot Store.
