# Phase 10H21 – Source Event Link Resolver

## Purpose
Phase 10H21 creates a **source event link resolver** only.  
It maps future source rows to canonical `event_id` values before line movement features are used.

## What it does NOT do
- It does **not** connect to vendors.
- It does **not** import paid data.
- It does **not** scrape.
- It does **not** write imported rows to SQLite.
- Ambiguous matches are **not** auto‑linked.

## Schema changes
Existing historical odds / results / line movement / experiment schemas are **unchanged**.

## Preparation
The resolver prepares the repo for **Phase 10H22 – As‑Of Line Movement Query Engine**.

## Roadmap checkpoint
Stop at **Phase 10H23 – Line Movement Data Quality Dashboard** before any real vendor / API / scraper connector.

## Next phase
**Phase 10H22** – As‑Of Line Movement Query Engine.
