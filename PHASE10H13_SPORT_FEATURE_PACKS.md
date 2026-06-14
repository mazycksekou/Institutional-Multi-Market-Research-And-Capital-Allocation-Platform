# Phase 10H13 – Sport Feature Packs

## Purpose

Sport Feature Packs are the sport‑level readiness layer of the repository.
This phase defines canonical feature packs for **every active sport surface**
tracked in the repo, not only the major sports.

## Scope

- Covers all sports present in source registry entries, existing modules,
  test files, and sport‑specific scripts.
- Some sports have **full‑depth packs** (backed by richer repo modules/tests).
- Other sports have **thin readiness packs** (basic odds and context).
- A **general fallback** pack provides minimum fields for unknown sport keys.

## Architecture

- All logic lives in `automation_scheduler/sport_feature_packs.py`.
- Streamlit displays **only** the backend summaries.
- No SQLite schema changes, no bankroll math changes, no backtest math changes.
- No scraping, no network calls, no new dependencies.
- **Leakage / settlement / result fields** are explicitly excluded from
  pre‑decision features (see `SPORT_FEATURE_NEVER_FEATURE_FIELDS`).
- Market‑specific feature packs are **not yet defined** (Phase 10H14).
- **Sportsbook** is not treated as a sport feature pack; it remains an
  odds/source/asset surface.

## Packs Structure

Each pack contains:

- `sport_key`
- `sport_family`
- `display_name`
- `depth_level` (`full`, `standard`, `thin`, `fallback`)
- `required_fields` – minimum fields needed for model testing
- `recommended_fields` – improve model quality but should not block testing
- `optional_fields` – extra fields that may be present
- `missing_data_warning` – human‑readable warning
- `operator_interpretation` – plain‑English description

## Readiness Evaluation

- `calculate_field_presence` counts present/missing per field.
- `evaluate_sport_feature_readiness` returns `readiness_level`:
  - **no_data** (0 rows)
  - **strong** (≥95% required, ≥60% recommended)
  - **usable** (≥80% required)
  - **thin** (≥50% required)
  - **not_ready** (below 50%)
- Leakage fields are never considered in pre‑decision features.

## Covered Sports

See `SPORT_FEATURE_PACKS` in the module for the full list (basketball,
baseball, football, soccer, hockey, tennis, golf, motorsports, cricket,
combat sports, esports, AFL, badminton, darts, handball, lacrosse,
pickleball, rugby, snooker, volleyball, water polo, and the fallback).

## Key Rules

- Never use leakage fields as model features.
- Do not enrich packs only because a sport appears in old design documents.
  Actual tracked source / tests / scripts / registry entries are stronger
  evidence.
- For repo‑thin sports, provide safe thin/default packs.

## Files Changed

- **Created** `automation_scheduler/sport_feature_packs.py` – canonical
  backend module with pack registry, normalisation helpers, and readiness
  functions.
- **Created** `tests/test_sport_feature_packs.py` – 15 tests covering
  normalisation, packs existence, field presence, readiness evaluation,
  and summary.
- **Modified** `automation_scheduler/streamlit_dashboard_data.py` – added
  import of sport feature pack functions and the
  `get_sport_feature_pack_snapshot_for_dashboard` helper.
- **Modified** `streamlit_app.py` – added a **Sport Feature Packs** section
  inside the Data Explorer tab.
- **Modified** `tests/test_streamlit_dashboard_data.py` – added imports
  and three tests for the snapshot helper, header text, and explanation text.
- **Created** `PHASE10H13_SPORT_FEATURE_PACKS.md` – this report.
