# Phase 10K2: Sports Odds Snapshot Pipeline Map and Cross-Sport Line Movement Foundation

## A. Executive Summary

Phase 10K2 is a validation-first sports odds snapshot foundation. It is not NFL-only and it does not start prediction testing.

This phase maps the existing sports odds and line movement owners, documents the future raw snapshot contract, and protects the decision-time leakage rule with tests. It adds no connectors, no API calls, no scraper logic, no paid data controls, no runtime CSV migration, no frontend changes, no sports model math changes, no bankroll math changes, and no Feature Ablation Lab behavior changes.

The current Streamlit main menu remains exactly:

- Feature Ablation Lab
- Bankroll Settings
- Instructions

Do not add vendor connectors. Do not start prediction testing.

## B. Existing Owner Validation

Do not assume existing owners work correctly. Each candidate below was reviewed from source and existing tests before deciding whether it fits 10K2.

| Candidate owner/module | Current purpose | Evidence inspected | Behavior proven by test/source | Fits 10K2 need? | Decision: use/extend/go around/document later | Risk |
|---|---|---|---|---|---|---|
| `research.market_research_schema` | 10K1 master research warehouse schema, including `raw_sports_odds` | Source: `research/market_research_schema.py`; tests: `tests/test_market_research_store.py` | `raw_sports_odds` has `sport`, `league`, `event_id`, `market`, `selection`, `odds_american`, `implied_probability`, `observed_at`, `source_key`, `source_name`, `source_file`, `inserted_at` | Partial | Document later schema expansion for `market_id`, `book`, `side`, `line`; do not create a second warehouse | Medium: current table cannot fully express side-aware line paths |
| `research.market_research_store` | Idempotent warehouse initialization and table inspection | Source and tests | Uses stdlib SQLite; no vendor/API/scraper imports; creates tables from schema | Partial | Use as future warehouse owner; do not extend in 10K2 | Low if schema expansion is planned before ingestion |
| `automation_scheduler.historical_odds_importers` | Canonical file importers for already-downloaded historical odds files | Source and `tests/test_historical_odds_importers.py` | Supports Football-Data soccer, MLB JSON, and SBR-style files; no network calls; stores decision-style odds rows | Partial | Document as legacy import owner; do not extend for raw snapshot path | Medium: canonical rows are not append-only raw book snapshots |
| `automation_scheduler.historical_odds_sqlite` | Legacy/local historical odds SQLite store | Source and `tests/test_historical_odds_sqlite.py` | Upserts events and odds; stores opening/closing odds fields when provided; query filters work | Partial | Keep for legacy behavior; do not replace or delete | Medium: upserted odds rows can collapse history and are not the 10K2 raw path |
| `automation_scheduler.historical_line_movement` | 10H12 line snapshot table and volatility helpers | Source and `tests/test_historical_line_movement.py` | Creates `historical_line_snapshots`; upsert by deterministic `snapshot_id`; supports opening/decision/current/closing labels | Partial | Use as existing line movement evidence; go around for raw append-only warehouse contract | Medium: id/upsert design is not raw append-only |
| `automation_scheduler.line_movement_import_contract` | Vendor-neutral line movement row contract and preview | Source and `tests/test_line_movement_import_contract.py` | Defines source/book/market/selection/line/odds/snapshot_time target shape; validates rows only | Yes for contract evidence | Reuse concepts; do not add ingestion or connector logic | Low |
| `authentication_scheduler.line_movement_import_contract` | Duplicate vendor-neutral line movement contract | Source comparison | Similar but separate copy exists under another package | Partial | Document duplicate candidate for later cleanup; do not delete in 10K2 | Medium: duplicated owner can drift |
| `automation_scheduler.source_event_link_resolver` | Resolves source rows to canonical `event_id` | Source-level evidence | No vendor calls; ambiguous matches are not auto-linked; source rows can be linked before as-of queries | Partial | Document as future event-id owner; no wiring now | Medium: raw snapshot path still needs canonical event policy |
| `automation_scheduler.asof_line_movement_query` | Read-only as-of query engine | Source and `tests/test_asof_line_movement_query.py` plus 10K2 targeted test | Filters snapshots with `snapshot_time <= hypothetical_bet_time`; selects latest available per group; reads SQLite without writing | Yes for leakage guard | Use as proven existing owner for future as-of behavior | Low |
| `automation_scheduler.line_movement_readiness` | Readiness inspection for historical line snapshot table | Source and `tests/test_line_movement_readiness.py` | Inspects schema and coverage; mentions as-of leakage guard; no vendor import | Partial | Document as readiness owner for old snapshot table, not raw warehouse | Low |
| `automation_scheduler.sport_feature_packs` | Cross-sport feature readiness registry | Source-level evidence and existing test presence | Covers major sports, soccer, tennis, golf, combat, cricket, motorsports, esports, and thin sports; blocks leakage fields | Yes for sport scope evidence | Use for repo-present sport list; do not alter | Low |
| `automation_scheduler.market_feature_packs` | Market-family readiness registry | Source-level evidence and existing test presence | Includes moneyline, spread/handicap, totals, team totals, props, combat, tennis, soccer specialty, live/alternate markets | Yes for market scope evidence | Use for main-market and later-prop map; do not alter | Low |
| `betting_providers.aliases` and `betting_providers.the_odds_api` | Live provider alias/sport key surface for The Odds API | Source only | Contains broad sport key list and HTTP adapter, but 10K2 does not call or wire it | Unknown for 10K2 runtime | Document only; do not import live data or add API calls | High if wired now |
| `automation_scheduler.provider_registry` | Provider/source registry and safety flags | Source-level evidence | Keeps provider write/execution disabled; sports and odds lanes exist | Partial | Use as source ownership evidence only | Low |
| `automation_scheduler.historical_backtest_bridge` | Converts historical odds rows to backtest rows | Source-level evidence | Builds pre-decision features and strips leakage fields; can run backtest if invoked | No for 10K2 | Document only; prediction testing remains deferred | Medium if accidentally invoked |
| `automation_scheduler.backtest_schema` / `backtest_leakage` | Backtest row aliases and leakage guards | Source and tests | Settlement, PnL, CLV, and closing line are blocked inside feature snapshots | Partial | Reuse rule language only; no new backtest run | Low |
| `automation_scheduler.feature_ablation_lab` | Current Feature Ablation Lab backend | Source and tests | Current lab behavior is heavily protected | No | Leave untouched | High if changed |
| `streamlit_app.py` | Current UI owner | Source text tests | Main menu is exactly Feature Ablation Lab, Bankroll Settings, Instructions | No | Leave untouched | High if changed |
| `quant_engine.py` and `risk_engine.py` | Sports math and bankroll/risk math | Source and tests | Odds, EV, Kelly, and stake behavior are existing owners | No | Leave untouched | High if changed |
| `settlement_rule_checker` / outcome modules | Settlement/rules evaluation | Source and tests | Settlement rules exist but are not pre-event feature owners | No for model features | Document leakage boundary; no wiring | Medium |

## C. Cross-Sport Coverage

Repo evidence does not contain an explicit production top liquidity ranking. Exact production liquidity ranking requires data/provider confirmation later. 10K2 therefore separates:

1. repo-present sport list
2. recommended top liquidity sports target list for later owner approval

### Repo-present Sport List

From `automation_scheduler.sport_feature_packs`, `betting_providers.aliases`, `main.py`, activation tests, and live smoke scripts:

- American sports: NFL (`americanfootball_nfl`), NCAAF (`americanfootball_ncaaf`), NBA (`basketball_nba`), WNBA (`basketball_wnba`), NCAAB (`basketball_ncaab`), NCAAW (`basketball_ncaaw`), MLB (`baseball_mlb`), NHL (`icehockey_nhl`).
- Additional American/provider-adjacent keys present: UFL/CFL football keys, AHL hockey, MILB, and college/baseball variants in provider aliases.
- soccer: global `soccer` feature pack, Football-Data importer, and many provider soccer leagues including EPL, MLS, Serie A, La Liga, Bundesliga, Ligue 1, UEFA, World Cup, Copa America, and others.
- tennis: `tennis` feature pack, tennis impact modules/tests, and ATP/WTA provider tournament keys.
- Other repo-present/configured sports: golf/PGA/LPGA, combat sports/UFC/MMA/boxing, cricket, NASCAR, Formula 1, Formula E, IndyCar, MotoGP, esports, AFL, badminton, darts, handball, lacrosse, pickleball, rugby, snooker, table tennis, volleyball, and water polo.

### Recommended Top Liquidity Sports Target List

This is recommended for later owner approval, not proven by repo liquidity data:

1. NFL
2. NBA
3. MLB
4. NHL
5. NCAAF
6. NCAAB
7. WNBA
8. Soccer, starting with EPL/MLS/Champions League/major international markets
9. Tennis, ATP/WTA main draw markets
10. UFC/MMA, with boxing as a documented adjacent combat target if provider coverage is stronger

The sports odds snapshot pipeline foundation is not NFL-only.

## D. Raw Snapshot Field Contract

Raw sports odds must be append-only timestamped snapshots. Each row represents one observed book/market/side/line/price at one time.

Required raw snapshot fields:

- `sport`
- `league`
- `event_id`
- `market_id`
- `book`
- `observed_at`
- `market`
- `side`
- `line`
- `odds_american`
- `implied_probability`
- `source_key`
- `source_name`
- `source_file`
- `inserted_at`

Later prop fields:

- `player_id`
- `player_name`
- `prop_type`
- `team`
- `opponent`

Prop fields are not required for main-market rows yet.

## E. Append-Only Storage Rule

The raw odds table is the path, not a current-state cache.

Good behavior:

- append-only timestamped snapshots
- no overwriting line history
- each observation preserves the book, market, side, line, price, source, and time seen
- current line is a derived view over raw history, not the raw table itself
- opening, decision, and closing lines are derived by time-window queries

Bad behavior:

- overwriting current line only
- losing intermediate line movement
- storing only open/current/close without raw path
- using future snapshots during a simulated decision

Existing `historical_line_snapshots` is useful but not a full raw append-only owner because it upserts by deterministic `snapshot_id`.

## F. Line Movement Path Features

Required future line movement outputs:

- `opening_line`: first snapshot for event/market/book or consensus, depending feature owner, and must be timestamped.
- `decision_line = latest snapshot at or before simulated decision time`.
- `closing_line`: latest available snapshot before event start.
- `movement_to_decision`: `decision_line - opening_line`.
- `closing_movement`: `closing_line - opening_line`.
- `min_line_seen`: minimum line observed during the allowed feature window.
- `max_line_seen`: maximum line observed during the allowed feature window.
- `largest_swing`: `max_line_seen - min_line_seen`.
- `largest_move_from_open`: largest absolute deviation from opening line during the allowed feature window.
- `movement_count`: number of distinct line changes during the allowed feature window.
- `first_move_time`: first timestamp where line changed from opening line.
- `last_move_time`: last timestamp where line changed before decision/close.
- `time_of_largest_move`: timestamp associated with largest absolute move.
- `book_consensus`: median line by default for first version.
- `book_count`: number of books contributing at decision time.
- `book_dispersion`: max line minus min line across books at decision time.
- `best_available_line`: best side-appropriate line available at or before decision time.
- `best_available_price`: best side-appropriate price at or before decision time.
- `sharp_book_delta`: future field only unless current repo already has proven sharp/public book grouping.

Consensus alternatives to document later: mean, mode, sharp book, or weighted consensus. For 10K2, median line is the default definition.

## G. Decision-Time Leakage Protection

Decision-time leakage protection is mandatory:

- model features may only use snapshots where `observed_at <= simulated_decision_time` or, for the existing 10H as-of owner, `snapshot_time <= hypothetical_bet_time`
- decision_line = latest snapshot at or before simulated decision time
- closing_line is evaluation-only unless decision time is closing time
- no future odds leakage
- post-decision snapshots cannot be model features
- settlement/results cannot be features
- `closing_line` is not a model input unless the simulated decision time is closing time

Existing as-of owner evidence:

- `automation_scheduler.asof_line_movement_query.is_snapshot_available_as_of` returns true only when snapshot time is at or before the hypothetical bet time.
- `select_latest_asof_snapshots` filters future snapshots before selecting latest available rows.
- `tests/test_asof_line_movement_query.py` already covers future exclusion.
- `tests/test_phase10k2_sports_snapshot_pipeline.py` adds a 10K2-specific proof that a future snapshot is not selected.

## H. Main Markets First / Props Later

Main markets first:

- moneyline
- spread
- total

These map to repo market-family evidence in `automation_scheduler.market_feature_packs`: `two_way_moneyline`, `three_way_moneyline`, `spread_or_handicap`, `runline`, `puckline`, `asian_handicap`, and `game_total`.

Props later:

- NFL QB passing yards
- NFL RB rushing yards
- NFL WR receiving yards
- basketball points/rebounds/assists
- baseball pitcher/batter props
- tennis player/game/set markets
- soccer player/handicap/total markets

10K2 does not build prop-specific logic. It only documents the later expansion path.

## I. Warehouse Compatibility

The 10K1 warehouse remains the canonical future research database. No second warehouse was created.

`raw_sports_odds` currently aligns with the timestamped snapshot idea on these basic fields:

- `sport`
- `league`
- `event_id`
- `market`
- `selection`
- `odds_american`
- `implied_probability`
- `observed_at`
- `source_key`
- `source_name`
- `source_file`
- `inserted_at`

Schema expansion deferred.

The table does not yet fully align with the 10K2 raw snapshot contract because it lacks:

- `market_id`
- `book`
- `side`
- `line`

Least-risk decision: do not alter the 10K1 warehouse in 10K2. The phase is validation-first and the existing schema can be documented without breaking `initialize_market_research_db` idempotency or creating migration ambiguity for existing SQLite files. A later schema phase should add these columns before any real raw odds snapshot ingestion is wired.

No schema changes were made in 10K2.

## J. No-Duplicate Decisions

| Function/table/helper | Existing owner exists? | Used, extended, bypassed, or documented? | Why |
|---|---|---|---|
| Raw sports odds storage | Yes: `research.market_research_schema.raw_sports_odds` | Documented | Canonical warehouse table exists but is missing fields; no duplicate table created |
| Legacy historical odds storage | Yes: `automation_scheduler.historical_odds_sqlite` | Documented | Existing upsert store is not raw append-only; kept untouched |
| Line movement snapshot storage | Yes: `automation_scheduler.historical_line_movement` | Documented | Useful old owner, but upserted labeled snapshots are not the raw append-only path |
| As-of line movement query | Yes: `automation_scheduler.asof_line_movement_query` | Used as proven behavior in tests | It already proves future snapshots are excluded |
| Line movement import contract | Yes: `automation_scheduler.line_movement_import_contract` | Documented | Contract vocabulary is useful; no ingestion added |
| Duplicate auth-package import contract | Yes: `authentication_scheduler.line_movement_import_contract` | Document later | Duplicate candidate only; no cleanup in this phase |
| Sport canonical scope | Yes: `automation_scheduler.sport_feature_packs`, `betting_providers.aliases`, `main.py` aliases | Used as source evidence | Provides cross-sport repo-present list |
| Market canonical scope | Yes: `automation_scheduler.market_feature_packs` | Used as source evidence | Provides main-market and props-later map |
| Feature building from line movement | Partial: volatility helpers and market/sport packs | Document later | Does not yet produce 10K2 features like `movement_count` or `best_available_line` |
| Backtest usage | Yes: `historical_backtest_bridge` and backtest schema | Bypassed | Prediction testing is deferred |
| Settlement/result handling | Yes: settlement and outcome modules | Bypassed for features | Settlement is evaluation-only, never pre-event feature input |

No duplicate code was deleted. No duplicate table was created.

## K. Testing Plan

Same-flow plan:

1. Add targeted tests first.
2. Run narrow test first after edits: `pytest tests/test_phase10k2_sports_snapshot_pipeline.py -q`.
3. Run full test: `pytest tests/`.
4. Run smoke: `python scripts/smoke_test.py`.
5. Run stat/ops check: `python scripts/ops_check.py`.
6. Commit only when clean.
7. Run test again after commit.
8. Run stat/ops check again.
9. Launch dash only if UI might be affected.

10K2 test coverage added:

- report exists and contains required sections/strings
- exact protected Streamlit main menu remains unchanged
- existing as-of owner excludes future snapshots
- backend snapshot modules do not import Streamlit or live connector libraries
- `raw_sports_odds` current alignment and schema gap are documented
- report does not claim forbidden implementation overreach

Per user instruction, tests were not run by Codex in this phase; the user will run tests and commit manually.

## L. Next Phase Impact

10K2 feeds later phases as follows:

- 10K3 Runtime/CSV Migration Plan: raw odds path and legacy SQLite behavior are now distinguished, so migration can be planned without deleting old paths.
- 10K4 0DTE Options Schema Foundation: decision-time leakage language carries over to options quotes and same-day option decisions.
- 10K5 Core Arbitrage Engine: book consensus, book dispersion, best line, and best price definitions are now documented before arbitrage uses them.
- 10K6 Frontend Navigation Expansion + Readiness Gate Check: UI expansion must preserve the existing main menu until explicitly approved.
- 10K8 Prediction Testing Phase: sports prediction testing should only begin after decision-time snapshot features are proven leakage-safe.

## Completion Notes

Files inspected for 10K2 included:

- `PHASE10K0_INSTITUTIONAL_REPO_AUDIT_AND_0DTE_SPECIFICITY_MAP.md`
- `PHASE10K1_UNIFIED_RESEARCH_WAREHOUSE_FOUNDATION.md`
- `research/market_research_schema.py`
- `research/market_research_store.py`
- `tests/test_market_research_store.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/historical_odds_importers.py`
- `automation_scheduler/historical_line_movement.py`
- `automation_scheduler/line_movement_import_contract.py`
- `authentication_scheduler/line_movement_import_contract.py`
- `automation_scheduler/asof_line_movement_query.py`
- `automation_scheduler/source_event_link_resolver.py`
- `automation_scheduler/line_movement_readiness.py`
- `automation_scheduler/sport_feature_packs.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/data_source_registry.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `automation_scheduler/backtest_schema.py`
- `automation_scheduler/settlement_rule_checker.py`
- `automation_scheduler/feature_ablation_lab.py`
- `streamlit_app.py`
- `main.py`
- `quant_engine.py`
- `betting_providers/aliases.py`
- `betting_providers/the_odds_api.py`

No connectors/API/external collection were added. No prediction testing started. The next recommended phase is a narrow schema owner phase for `raw_sports_odds` contract completion, followed by the planned runtime/CSV migration work.
