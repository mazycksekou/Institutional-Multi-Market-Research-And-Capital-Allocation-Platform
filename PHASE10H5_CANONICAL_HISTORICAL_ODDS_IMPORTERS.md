# Phase 10H5 – Canonical Historical Odds Importers

## Status

Completed.  This phase delivers a registry of importers that convert raw
historical odds/results files (CSV/JSON) into a **canonical** row format,
without any SQLite storage, downloading, scraping, or network calls.

## What this phase includes

- **`automation_scheduler/historical_odds_importers.py`** – the core module that
  defines:
  - Canonical required/optional field names.
  - Odds‑conversion helpers (`american_to_implied_probability`,
    `decimal_to_implied_probability`, `odds_to_implied_probability`).
  - Team/market/selection normalisers.
  - `build_canonical_historical_odds_row(…)` – builder for canonical rows.
  - `validate_canonical_historical_odds_row(…)` – checks required fields,
    numeric bounds, and decision‑time feature leakage.
  - Three concrete importers:
    1. **Football‑Data.co.uk CSV** – maps standard soccer columns (Div, Date,
       HomeTeam, AwayTeam, FTHG, FTAG, FTR, B365*/Avg*/Max*) to canonical rows.
    2. **ArnavSaraogi MLB Odds Scraper JSON** – flexible JSON importer that
       discovers events, bookmakers, markets, and outcomes.
    3. **SportsbookReview‑style CSV/JSON** – safe starter importer for free‑form
       SBR data.
  - `import_historical_odds_file(source_key, path)` – router that dispatches to
    the correct importer based on the source key.
  - `summarize_imported_historical_rows(rows)` – returns a dict with projection
    readiness, missing‑field count, warnings, etc.
  - `get_supported_importer_keys()` – returns the list of supported source keys.
- **`tests/test_historical_odds_importers.py`** – >10 test cases that cover:
  - Football‑Data CSV producing three canonical rows (home/draw/away).
  - Football‑Data rows carrying correct sport, market, and implied probabilities.
  - MLB JSON producing two moneyline outcomes.
  - SBR CSV producing one row.
  - American (positive & negative) and decimal odds conversion.
  - Validation failing on missing required fields.
  - Validation warning on leaking fields in `features_known_at_decision_time`.
  - Router routing to the correct importer for each supported key.
  - Unknown source key raising `ValueError`.
  - Summary returning `projection_ready=True` for valid rows.

## Design principles

- **No SQLite yet.**  Phase 10H6 will introduce the SQLite historical odds
  store.  This phase deliberately keeps importers free of any database writes.
- **No downloads/scraping.**  All importers assume a local file already exists.
- **Decision‑time vs. final‑result separation.**  Canonical rows distinguish
  odds known at decision time (`odds_at_decision_time`,
  `features_known_at_decision_time`) from final‑result fields
  (`final_result`, `winner`, `home_score`, `away_score`, `profit_loss`).
  The validator flags any attempt to supply such result fields inside
  `features_known_at_decision_time`.

## Next phase (Phase 10H6)

Add SQLite historical odds store.  This store will consume the canonical rows
produced by the importers above.

## First real sources to test later

1. **Football‑Data.co.uk CSV** – most important; the cleanest first source for
   historical odds/results backtesting.
2. **ArnavSaraogi MLB Odds Scraper JSON** – second priority.
3. **SportsbookReview‑style data** – third priority (needs validation).
