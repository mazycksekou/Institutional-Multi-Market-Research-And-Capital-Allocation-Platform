# Phase 10H22 – As‑Of Line Movement Query Engine

**Phase 10H22** creates an **as‑of line movement query engine** only.

It filters historical snapshots to `snapshot_time ≤ hypothetical_bet_time`.  
This prevents **look‑ahead bias** by ensuring that only snapshots known **at or before** the hypothetical bet time are used.

It uses the **resolved `event_id`** from Phase 10H21.

## What it does NOT do

- Does **not** connect to vendors.
- Does **not** import paid data.
- Does **not** scrape.
- Does **not** write imported rows to SQLite.
- Does **not** alter existing historical odds/results/line movement/experiment schemas.

## Roadmap checkpoint

Stop at Phase 10H23 (**Line Movement Data Quality Dashboard**) before any real vendor/API/scraper connector.

## Next phase

Phase 10H23 – Line Movement Data Quality Dashboard.
