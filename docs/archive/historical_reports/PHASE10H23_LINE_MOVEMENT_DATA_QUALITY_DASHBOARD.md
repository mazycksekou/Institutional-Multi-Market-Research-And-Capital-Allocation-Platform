# Phase 10H23 – Line Movement Data Quality Dashboard

**Status:** Checkpoint created.  
**Version:** 10H23  

## Purpose

Phase 10H23 creates the required line movement data quality checkpoint dashboard.  
It shows coverage, missing event links, duplicate snapshots, sports, markets, books, as‑of safety, and readiness.

## Key constraints

- It does **not** connect to vendors.
- It does **not** import paid data.
- It does **not** scrape.
- It does **not** write imported rows to SQLite.
- Existing historical odds, results, line movement, and experiment schemas are unchanged.

## What the dashboard shows

| Metric | Description |
|--------|-------------|
| **Coverage** | Total snapshots, linked/unlinked counts, counts of missing key fields (event_id, snapshot_time, market_family, bookmaker, sport, market, selection). |
| **Missing event links** | Rows where event_id is blank/null. These must be resolved before line movement features are trusted. |
| **Duplicate snapshots** | Groups of rows that share the same event_id, bookmaker, market_family, market, selection, snapshot_label, and snapshot_time. Duplicates must be reviewed before connector work. |
| **Sports / Markets / Books** | Distinct values and per‑group snapshot counts for sport, market_family, bookmaker, and market. |
| **As‑of query safety** | When a hypothetical_bet_time is supplied, counts of available, future, and invalid‑time snapshots. Filtering must use `snapshot_time ≤ hypothetical_bet_time` to avoid look‑ahead bias. |
| **Readiness** | A stable `ready` flag (True only when all preconditions are met), a `readiness_level` (strong / usable / blocked), and a list of reasons for any block. |

## Checkpoint meaning

This is the required stop/review point before any real vendor, API, scraper, or paid data connector is added.

**Missing links must be resolved before line movement features are trusted.**  
**Duplicate snapshots must be reviewed before connector work.**  
**As‑of filtering must use `snapshot_time ≤ hypothetical_bet_time` to avoid look‑ahead bias.**

## Next phase (after review)

Phase **10H24** – First Real Data Connector Spike.  
After this checkpoint is reviewed and the dashboard is healthy (all preconditions met), Phase 10H24 may begin the first real data connector spike.
