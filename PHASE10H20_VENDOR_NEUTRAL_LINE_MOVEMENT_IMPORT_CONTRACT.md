# Phase 10H20 – Vendor‑Neutral Line Movement Import Contract

## Overview

Phase 10H20 defines a **vendor‑neutral import contract** for future line movement sources.  
It does **not** connect to vendors.  
It does **not** import paid data.  
It does **not** scrape any external site.  
It validates and previews rows only, preparing the repository for real data ingestion that will happen in Phase 10H21 and later.

## What this phase delivers

- A canonical set of input fields that any future source must provide.
- Required / optional field classification.
- Normalisation helpers for:
  - market family (two‑way moneyline, three‑way moneyline, spread/handicap, game total, team total, player prop, general market)
  - snapshot label (opening, current, decision, closing, unknown)
  - generic value conversion to safe JSON strings.
- Deterministic `snapshot_id` generation.
- Validation of a single vendor‑neutral row.
- Batch preview with validity counts.
- A human‑readable contract description.

## What this phase does NOT do

- Build any real vendor connector.
- Add paid data logic.
- Add scraper logic.
- Call any external API.
- Fetch data from the internet.
- Add dependencies.
- Alter the `historical_odds` or `historical_odds_sqlite` schema.
- Alter bankroll math.
- Re‑run model tests.
- Write imported rows into SQLite.

## Roadmap checkpoint

> **Stop at Phase 10H23** (Line Movement Data Quality Dashboard) **before** building any real vendor/API/scraper connector.

## Next phase

**Phase 10H21 – Source Event Link Resolver** will resolve `source_event_id` to a canonical `event_id`, making the snapshots ready for insertion.

## Mapping to existing schema

The canonical output of this contract is a dict that mirrors the `historical_line_snapshots` table created in **Phase 10H12**.  
The `line_movement_readiness` layer from **Phase 10H19** will inspect the table once it is populated later.

## Unchanged artifacts

- `historical_odds_sqlite` – unchanged.
- `historical_line_movement` – unchanged (the table already exists; this contract does not insert).
- `experiment_history_store` – unchanged.
- All tests for earlier phases – unchanged.
