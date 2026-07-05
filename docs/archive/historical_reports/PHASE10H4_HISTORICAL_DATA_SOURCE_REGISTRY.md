# Phase 10H4: Historical Data Source Registry + Model Projection Source Ranking

## Source Decisions

### Keep
- **Football-Data.co.uk** (`football_data_uk`) – soccer CSV, cleanest first source.
- **ArnavSaraogi MLB Odds Scraper** (`arnav_mlb_odds_scraper`) – MLB JSON odds.
- **SportsbookReview Scraper Dataset** (`sportsbookreview_scraper`) – NFL, NBA, MLB, NHL baseline, needs validation.

### Keep as Tool (not first importer)
- **OddsHarvester** (`odds_harvester`) – scraper tool, useful later but fragile.

### Downgrade
- **DataHub football data** – lower priority than Football‑Data.co.uk.
- **georgedouzas sports‑betting** – not a historical odds source.
- **oddor** – limited scope.
- **Kaggle mixed betting datasets** – require case‑by‑case approval.

### Remove
- **Medium articles**, **Reddit threads**, **Generic CSV‑to‑SQLite forum posts** – not data sources.

## Why SQLite Comes After Importers

SQLite storage is deliberately deferred to **Phase 10H6**. It makes no sense to build storage before we have reliable canonical importers. Phase 10H5 will create the importers; Phase 10H6 will write their output into SQLite.

## Next Phases

- **Phase 10H5** – Canonical historical odds importers (Football‑Data.co.uk first).
- **Phase 10H6** – SQLite historical odds store.
