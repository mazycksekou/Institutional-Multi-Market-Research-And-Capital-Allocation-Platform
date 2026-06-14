# Phase 10H14 – Market Feature Packs

## Purpose

Market Feature Packs are the market‑level readiness layer of the repository.
This phase defines canonical feature packs for every active market family
tracked in the repo, not only the basic win markets.

## Scope

- Covers winner, spread, total, prop, combat, futures, motorsport, golf,
  esports, soccer specialty, cricket, tennis, live, and alternate‑line
  market families.
- Some market families have **full‑depth packs** (backed by richer data).
- Others have **thin readiness packs** (basic odds and context).
- A **general fallback** pack provides minimum fields for unknown market keys.

## Architecture

- All logic lives in `automation_scheduler/market_feature_packs.py`.
- Streamlit displays **only** the backend summaries.
- No SQLite schema changes, no bankroll math changes, no backtest math changes.
- No scraping, no network calls, no new dependencies.
- **Leakage / settlement / result fields** are explicitly excluded from
  pre‑decision features (see `MARKET_FEATURE_NEVER_FEATURE_FIELDS`).
- Market‑specific feature packs are separate from **Sport Feature Packs**
  (Phase 10H13). Later phases can combine Sport + Market readiness into
  strategy filters and model experiment profiles.

## Packs Structure

Each pack contains:

- `market_family`
- `display_name`
- `depth_level` (`full`, `standard`, `thin`, `fallback`)
- `required_fields` – minimum fields needed for model testing
- `recommended_fields` – improve model quality but should not block testing
- `optional_fields` – extra fields that may be present
- `missing_data_warning` – human‑readable warning
- `operator_interpretation` – plain‑English description

## Readiness Evaluation

- `calculate_market_field_presence` counts present/missing per field.
- `evaluate_market_feature_readiness` returns `readiness_level`:
  - **no_data** (0 rows)
  - **strong** (≥95% required, ≥60% recommended)
  - **usable** (≥80% required)
  - **thin** (≥50% required)
  - **not_ready** (below 50%)
- Leakage fields are never considered in pre‑decision features.

## Covered Markets

See `MARKET_FEATURE_PACKS` in the module for the full list (winner,
spread/handicap, runline, puckline, totals, player props, combat,
outrights/futures, motorsports/golf, esports, soccer specialty, cricket,
tennis, live/alternate, and the fallback).

## Key Rules

- Never use leakage fields as model features.
- Do not enrich packs only because a market appears in old design documents.
  Actual tracked source / tests / scripts / registry entries are stronger
  evidence.
- For repo‑thin markets, provide safe thin/default packs.

## Files Changed

- **Created** `automation_scheduler/market_feature_packs.py` – canonical
  backend module with pack registry, normalisation helpers, and readiness
  functions.
- **Created** `tests/test_market_feature_packs.py` – 17 tests covering
  normalisation, packs existence, field presence, readiness evaluation,
  and summary.
- **Modified** `automation_scheduler/streamlit_dashboard_data.py` – added
  import of market feature pack functions and the
  `get_market_feature_pack_snapshot_for_dashboard` helper.
- **Modified** `streamlit_app.py` – added a **Market Feature Packs** section
  inside the Data Explorer tab.
- **Modified** `tests/test_streamlit_dashboard_data.py` – added imports
  and three tests for the snapshot helper, header text, and explanation text.
- **Created** `PHASE10H14_MARKET_FEATURE_PACKS.md` – this report.
