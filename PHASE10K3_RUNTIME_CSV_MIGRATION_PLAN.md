# Phase 10K3: Runtime/CSV Migration Plan and Storage Owner Validation

## A. Executive Summary

Phase 10K3 is a validation-only phase. This Runtime/CSV Migration Plan inventories the current file, CSV, JSON, JSONL, SQLite, and report-artifact owners before any warehouse migration work begins. The target warehouse remains `research/market_research.db`, owned by `research.market_research_store` and defined by `research.market_research_schema`.

No migration was executed in this phase. No runtime files were deleted. No CSV paths were deleted. Existing sports SQLite flow was not replaced. Duplicate storage owners are tracked, not deleted.

Important guardrails for this phase:

- Do not add vendor connectors.
- Do not start prediction testing.
- Do not alter Streamlit main menu.
- Do not delete runtime, CSV, JSON, JSONL, or SQLite stores during inventory.
- Asset-grade cleanup happens later.

The current Streamlit main menu remains exactly: Feature Ablation Lab, Bankroll Settings, Instructions.

## B. Storage Owner Validation

| Candidate owner/module | Current storage role | Evidence inspected | Behavior proven by test/source | Active/Wired? | Fits future warehouse plan? | Decision | Risk |
|---|---|---|---|---|---|---|---|
| `automation_scheduler.data_paths` | Canonical runtime data-root resolver and confinement guard | `AUTOMATION_DATA_DIR`, `get_automation_data_dir`, `get_runtime_data_path`, runtime directory helpers | Source rejects absolute path parts and path escape attempts; tests exist in `tests/test_data_paths.py` | Yes. Imported by `main.py`, scheduler modules, bankroll state, report writers, paper ledger | Yes, as the runtime owner until warehouse writes are added | Keep current canonical | Low if retained; high if bypassed by ad hoc paths |
| `src.services.bet_csv_service` | Service owner for `data/bets.csv` | `BETS_FILE = DATA_DIR / "bets.csv"`, `append_bet`, `summarize_bets` | Source appends CSV rows, rewrites header when row shape expands, summarizes ROI/wins/losses | Yes. Imported by `main.py` and route layer | Partial. Maps to `backtest_trades`, `settlements`, and a later sports bet/order table | Migrate later with mirror writes | Medium: active ledger could diverge from JSONL bet log |
| `src.api.bet_csv_routes` | API route currently writes and reads `BETS_FILE` directly | Route imports `BETS_FILE`, uses `csv.DictWriter`, uses `pd.read_csv(BETS_FILE)` | Source proves a second writer/reader around the same CSV | Yes. Registered by `main.py` through `register_bet_csv_routes` | Partial. Should eventually call one owner and mirror to warehouse | Needs owner decision | Medium: duplicate owner around `bets.csv` |
| `bet_log.py` | JSONL bet decision, result, CLV, and bankroll ledger | `BET_LOG_PATH = Path("data") / "bet_log.jsonl"` | Tests in `tests/test_bet_log.py` append, read, update results, and summarize performance | Yes. Injected into betting action routes by `main.py` | Partial. Maps to `backtest_trades`, `settlements`, `performance_metrics`, and later live/paper bet table | Migrate later | Medium: overlaps with `bets.csv` but richer settlement fields |
| `automation_scheduler.historical_odds_sqlite` | Existing sports SQLite flow for historical odds | Tables `source_imports`, `historical_events`, `historical_odds`, `historical_results` | Tests in `tests/test_historical_odds_sqlite.py`; source initializes and upserts canonical odds rows | Yes. Used by dashboard data and historical backtest bridge | Partial. Maps to `raw_sports_odds`, with source metadata gaps | Keep current canonical until mirror phase | High if replaced too early |
| `automation_scheduler.historical_line_movement` | Existing line movement table in the sports SQLite store | `historical_line_snapshots`, `initialize_line_movement_schema`, query/summary helpers | Tests in `tests/test_historical_line_movement.py` create table, upsert rows, summarize readiness | Yes. Used by dashboard/as-of/data-quality paths | Partial. Maps to `raw_sports_odds` now, or later `raw_sports_line_snapshots` | Mirror later | Medium: append-only line history must not be collapsed |
| `automation_scheduler.historical_odds_importers` | CSV/JSON source importer, not a final storage owner | Football CSV, MLB JSON, SBR CSV/JSON import functions | Source parses local files and emits canonical rows for SQLite import | Yes. Called by `import_historical_odds_file_to_sqlite` | Yes as a pre-warehouse ingest adapter | Keep current canonical | Low if adapter remains file-to-row only |
| `automation_scheduler.streamlit_dashboard_data` | Dashboard file/SQLite access facade and export helpers | Defaults for dashboard JSON, canonical JSONL, paper ledger, review queue, system health, historical SQLite, upload dir | Source reads JSON/JSONL, writes dashboard JSON/MD, saves uploads, connects SQLite | Yes. Imported by `streamlit_app.py` | Partial. Must remain UI facade while warehouse read paths are added | Keep current canonical | Medium: has many path constants |
| `automation_scheduler.paper_trade_ledger` | Legacy paper-trade JSON ledger | `data/paper_ledger/paper_ledger.json`, `load_paper_ledger`, `create_paper_entry`, settle/update helpers | Tests in `tests/test_paper_trade_ledger.py` load/create/update/summarize | Yes | Partial. Maps to `backtest_trades`, `settlements`, `performance_metrics` | Migrate later | Medium: overlaps with paper decisions |
| `automation_scheduler.paper_decision_ledger` | Paper decision ledger with latest/items and legacy file | `data/paper_ledger/latest.json`, `data/paper_ledger/items/*.json`, `data/paper_ledger/paper_decisions.json` | Source loads latest, items, and legacy file; scheduler/calibration persist decisions | Yes. Used by `scheduler_runner` and `calibration_collector` | Partial. Maps to `backtest_runs`, `backtest_trades`, `settlements`, `performance_metrics` | Migrate later | Medium: multiple files inside same logical owner |
| `automation_scheduler.review_queue` | Review queue runtime JSON owner | `data/review_queue/latest.json`, `data/review_queue/items/*.json`, `data/review_queue/review_queue.json` | Source persists latest, per-run item file, and legacy queue | Yes. Scheduler and API health paths read it | Partial. Mostly an operator artifact, with some fields eligible for `model_predictions` | Export artifact | Medium: not all review fields belong in warehouse |
| `automation_scheduler.outcome_store` | Outcome/settlement runtime JSON owner | `data/outcomes/latest.json`, `data/outcomes/items/*.json`, `data/outcomes/outcomes.json` | Tests in `tests/test_outcome_store.py` cover loading, persistence, dedupe, invalid status | Yes. Used by calibration collector and outcomes endpoints | Yes. Maps to `settlements` | Migrate later | Medium: settlement identity must be deduped before mirroring |
| `automation_scheduler.calibration_collector` | Collector scheduler files, watchlists, daily files, cycle reports | `data/collector_scheduler`, watchlists, completed index, daily JSON/MD, `latest_cycle.json` | Tests in `tests/test_calibration_collector.py` cover watchlists and daily reports | Yes | Partial. Some rows map to `raw_prediction_markets`, `settlements`, `model_predictions`; many remain runtime control artifacts | Needs owner decision | Medium: control-plane files should not be forced into market warehouse |
| `automation_scheduler.experiment_history_store` | SQLite table for ablation/calibration history | `experiment_history_runs` created in caller-supplied SQLite path | Tests in `tests/test_experiment_history_store.py` cover initialize/save/list/get/compare | Yes. Used by Feature Ablation Lab history UI | Partial. Maps to `backtest_runs` and `performance_metrics`, with export artifacts kept separately | Migrate later | Medium: currently shares the selected historical SQLite path in Streamlit |
| `automation_scheduler.experiment_report_exporter` | Markdown export builder for experiment history | Builds markdown and filenames; source says export does not write files directly | Tests in `tests/test_experiment_report_exporter.py` cover markdown export | Yes, through Streamlit download path | No table target by default | Export artifact | Low |
| `automation_scheduler.strategy_performance_ledger` | Strategy performance JSON ledger | `data/strategy/performance_ledger.json` | Source appends/redacts records and summarizes strategy performance | Partial/yes through strategy framework | Yes. Maps to `performance_metrics` | Migrate later | Medium: strategy IDs must map cleanly to model/run IDs |
| `automation_scheduler.data_source_registry` | Data source registry reports and research-lane artifacts | `data/data_sources/latest.json`, `items/*.json`, `latest.md`, research lane JSON/MD | Source writes registry snapshots and markdown summaries | Yes via automation data source endpoints | Partial. Needs source metadata table in warehouse | Needs owner decision | Medium: no current `market_research.db` source registry table |
| `config.py` | Legacy path constants | `data/stock_log.csv`, `data/analysis_log.csv`, `data/bets.csv` | Source defines legacy app config paths | Unknown active use by scan; `bets.csv` overlaps active service | Partial. Stocks map to `raw_equity_prices`; analysis may map to `performance_metrics` or artifact storage | Unknown / needs owner decision | Medium: legacy config paths can drift from runtime data root |
| `research.market_research_store` | Future warehouse store owner | `DEFAULT_DB_FILENAME = "market_research.db"`, initialize/list/table helpers | Tests in `tests/test_market_research_store.py` prove import safety, idempotent init, schema tables | Yes as target owner | Yes | Keep current canonical | Low if schema is only expanded through tests |

## C. Runtime/CSV Inventory

| File/module | Function/class/constant/path | Storage type | Current purpose | Active/Wired? | Test coverage | Current owner | Future warehouse target | Migration decision | Risk |
|---|---|---|---|---|---|---|---|---|---|
| `src/services/bet_csv_service.py` | `data/bets.csv`, `BETS_FILE`, `append_bet`, `summarize_bets` | CSV | Bet ledger and ROI summary | Yes | Service behavior covered indirectly by API/path tests; new 10K3 report guard | `src.services.bet_csv_service` | `backtest_trades`, `settlements`, later sports bet/order table | Migrate later | Medium |
| `src/api/bet_csv_routes.py` | `BETS_FILE`, `csv.DictWriter`, `pd.read_csv(BETS_FILE)` | CSV route access | API append and summary over same CSV | Yes | Route coverage exists in API tests by repo pattern; 10K3 documents duplicate owner | `src.api.bet_csv_routes` | Same as `bets.csv` | Needs owner decision | Medium |
| `bet_log.py` | `data/bet_log.jsonl`, `append_bet_log_entry`, `update_bet_result` | JSONL | Bet decisions, status, P/L, CLV, bankroll summaries | Yes | `tests/test_bet_log.py` | `bet_log.py` | `backtest_trades`, `settlements`, `performance_metrics` | Migrate later | Medium |
| `automation_scheduler/data_paths.py` | `get_runtime_data_path`, `get_automation_data_dir`, `AUTOMATION_DATA_DIR` | Runtime root helper | Canonical path resolution and confinement | Yes | `tests/test_data_paths.py`; 10K3 source guard | `automation_scheduler.data_paths` | Not a table; remains path control owner | Keep current canonical | Low |
| `automation_scheduler/scheduler_config.py` | `paths.review_queue`, `paths.paper_ledger`, `paths.outcomes`, `paths.collector_scheduler`, `paths.institutional_lab`, `paths.system_health`, `paths.performance_reports` | Runtime directories | Scheduler path registry | Yes | `tests/test_scheduler_config.py`, scheduler tests | `automation_scheduler.scheduler_config` | Mixed: warehouse for facts, artifacts for control reports | Keep current canonical | Medium |
| `automation_scheduler/paper_trade_ledger.py` | `data/paper_ledger/paper_ledger.json` | JSON | Legacy paper-trade ledger | Yes | `tests/test_paper_trade_ledger.py` | `automation_scheduler.paper_trade_ledger` | `backtest_trades`, `settlements`, `performance_metrics` | Migrate later | Medium |
| `automation_scheduler/paper_decision_ledger.py` | `data/paper_ledger/latest.json`, `data/paper_ledger/items/*.json`, `data/paper_ledger/paper_decisions.json` | JSON | Paper decision ledger and per-run artifacts | Yes | `tests/test_paper_decision_ledger.py` | `automation_scheduler.paper_decision_ledger` | `backtest_runs`, `backtest_trades`, `settlements`, `performance_metrics` | Migrate later | Medium |
| `automation_scheduler/review_queue.py` | `data/review_queue/latest.json`, `items/*.json`, `review_queue.json` | JSON | Operator review queue | Yes | `tests/test_review_queue.py`, scheduler tests | `automation_scheduler.review_queue` | `model_predictions` for scored candidates; artifact storage for queue state | Export artifact | Medium |
| `automation_scheduler/outcome_store.py` | `data/outcomes/latest.json`, `items/*.json`, `outcomes.json` | JSON | Outcome and settlement records | Yes | `tests/test_outcome_store.py` | `automation_scheduler.outcome_store` | `settlements` | Migrate later | Medium |
| `automation_scheduler/calibration_collector.py` | `data/collector_scheduler/watchlists/*.latest.json`, `settled_completed.index.json`, `daily/*.json`, `latest_cycle.json`, `items/*.json` | JSON/MD | Calibration collector state and reports | Yes | `tests/test_calibration_collector.py` | `automation_scheduler.calibration_collector` | `raw_prediction_markets`, `settlements`, `model_predictions`, plus artifact storage | Needs owner decision | Medium |
| `automation_scheduler/bankroll_state.py` | `get_runtime_data_path("bankroll")` | JSON | Bankroll settings/state | Yes | `tests/test_bankroll_state.py` | `automation_scheduler.bankroll_state` | Later bankroll/risk table or artifact storage | Needs owner decision | Low |
| `automation_scheduler/historical_odds_sqlite.py` | `source_imports`, `historical_events`, `historical_odds`, `historical_results` | SQLite | Existing sports SQLite flow for imported historical odds | Yes | `tests/test_historical_odds_sqlite.py` | `automation_scheduler.historical_odds_sqlite` | `raw_sports_odds`; missing source metadata table | Keep current canonical, mirror later | High |
| `automation_scheduler/historical_line_movement.py` | `historical_line_snapshots` | SQLite table | Append-style line movement snapshots and readiness | Yes | `tests/test_historical_line_movement.py` | `automation_scheduler.historical_line_movement` | `raw_sports_odds` or future `raw_sports_line_snapshots` | Mirror later | Medium |
| `automation_scheduler/streamlit_dashboard_data.py` | `data/historical/historical_odds.db`, `data/historical/uploads`, dashboard JSON/MD, canonical JSONL | SQLite/JSON/JSONL/MD | Dashboard data facade, imports, projections, exports | Yes | `tests/test_streamlit_dashboard_data.py` | `automation_scheduler.streamlit_dashboard_data` | Mixed warehouse read/write facade plus artifacts | Keep current canonical | Medium |
| `automation_scheduler/backtest_dataset_builder.py` | `data/backtests/canonical/latest.jsonl`, `schema_report.json` | JSONL/JSON | Canonical backtest dataset artifact | Yes | `tests/test_backtest_dataset_builder.py` | `automation_scheduler.backtest_dataset_builder` | `backtest_runs`, `backtest_trades`, `performance_metrics` | Migrate later | Medium |
| `automation_scheduler/backtesting_engine.py` | `data/backtests`, `data/clv`, `data/calibration`, `data/performance_reports` | JSON | Replay, CLV, calibration, performance artifacts | Yes | `tests/test_backtesting_engine.py` | `automation_scheduler.backtesting_engine` | `backtest_runs`, `backtest_trades`, `performance_metrics`, artifact storage | Migrate later | Medium |
| `automation_scheduler/model_performance_report.py` | `data/performance_reports/*.json` | JSON | Model performance reports | Yes | `tests/test_model_performance_report.py` | `automation_scheduler.model_performance_report` | `performance_metrics`; artifact storage | Migrate later | Low |
| `automation_scheduler/experiment_history_store.py` | `experiment_history_runs` | SQLite | Feature ablation and calibration history | Yes | `tests/test_experiment_history_store.py` | `automation_scheduler.experiment_history_store` | `backtest_runs`, `performance_metrics` | Migrate later | Medium |
| `automation_scheduler/experiment_report_exporter.py` | Markdown export content, no direct write | Export artifact | Offline operator review pack | Yes | `tests/test_experiment_report_exporter.py` | `automation_scheduler.experiment_report_exporter` | No direct warehouse table | Export artifact | Low |
| `automation_scheduler/strategy_performance_ledger.py` | `data/strategy/performance_ledger.json` | JSON | Strategy performance ledger | Partial/yes | Strategy framework tests | `automation_scheduler.strategy_performance_ledger` | `performance_metrics` | Migrate later | Medium |
| `automation_scheduler/audit_ledger.py` | `data/security/audit/*.json` | JSON | Security audit records | Yes | Security tests | `automation_scheduler.audit_ledger` | Artifact storage or governance table later | Export artifact | Low |
| `automation_scheduler/institutional_audit_ledger.py` | `data/institutional_lab/audit/*.json` | JSON | Institutional audit records | Yes | `tests/test_institutional_audit_ledger.py` | `automation_scheduler.institutional_audit_ledger` | Artifact storage or governance table later | Export artifact | Low |
| `automation_scheduler/report_writer.py` | `config["paths"]["reports"]/scheduler_run_*.json` | JSON | Scheduler run report | Yes | Scheduler tests | `automation_scheduler.report_writer` | `backtest_runs`/artifact storage depending row type | Export artifact | Low |
| `automation_scheduler/system_health.py` | `data/system_health/health.json` | JSON | Runtime health snapshot | Yes | `tests/test_system_health.py` | `automation_scheduler.system_health` | No market table | Export artifact | Low |
| `automation_scheduler/data_source_registry.py` | `data/data_sources/latest.json`, `items/*.json`, `latest.md`, `research_lanes.latest.json` | JSON/MD | Source registry and research lanes | Yes | `tests/test_data_source_registry.py` | `automation_scheduler.data_source_registry` | Missing `source_registry` or `source_imports` table | Needs owner decision | Medium |
| `automation_scheduler/open_sports_history_import.py` | Validated open sports import reports and grouped JSON | JSON/MD | Validated open-data preview rows and reports | Yes | `tests/test_open_sports_history_import.py` | `automation_scheduler.open_sports_history_import` | `raw_sports_odds`, source registry table later | Migrate later | Medium |
| `config.py` | `data/stock_log.csv`, `data/analysis_log.csv`, `data/bets.csv` | CSV paths | Legacy app path constants | Unknown active | None specific in this phase | `config.Config` | `raw_equity_prices`, `performance_metrics`, `backtest_trades` | Unknown / needs owner decision | Medium |

## D. Warehouse Target Map

| Current storage concept | Current path/module | Future market_research.db table | Missing fields/tables if any | Later phase | Notes |
|---|---|---|---|---|---|
| Sports odds imported rows | `historical_odds_sqlite.historical_odds` | `raw_sports_odds` | 10K2 deferred fields such as book, side, line, market_id; richer source import metadata | 10K4/10K6 | Mirror only after field parity tests |
| Sports events/results | `historical_events`, `historical_results` | `raw_sports_odds`, `settlements` | Event dimension and source import table may be needed | 10K6 | Do not replace existing sports SQLite flow yet |
| Line movement snapshots | `historical_line_snapshots` | `raw_sports_odds` or future `raw_sports_line_snapshots` | Dedicated snapshot table may be cleaner for append-only movement | 10K4/10K6 | Must preserve decision-time leakage controls |
| CSV bet ledger | `data/bets.csv` | `backtest_trades`, `settlements`, `performance_metrics` | Later sports bet/order table for live/paper bet lifecycle | 10K6 | Mirror writes before switching reads |
| JSONL bet log | `data/bet_log.jsonl` | `backtest_trades`, `settlements`, `performance_metrics` | Later sports bet/order table; ID reconciliation with `bets.csv` | 10K6 | Compare old vs warehouse rows before any switch |
| Paper trade ledger | `data/paper_ledger/paper_ledger.json` | `backtest_trades`, `settlements`, `performance_metrics` | Paper/live trade type discriminator | 10K6 | Candidate for deletion after migration tests only |
| Paper decision ledger | `data/paper_ledger/latest.json`, `items/*.json`, `paper_decisions.json` | `backtest_runs`, `backtest_trades`, `settlements`, `performance_metrics` | Paper decision/event table may be needed | 10K6 | Keep latest/items until read parity is proven |
| Review queue | `data/review_queue/latest.json`, `items/*.json`, `review_queue.json` | `model_predictions` for scored candidates; artifact storage for queue state | Queue-specific operator state table may be needed | 10K6 | Not all queue fields should be normalized now |
| Outcomes | `data/outcomes/latest.json`, `items/*.json`, `outcomes.json` | `settlements` | Source/event identity normalization | 10K6 | Must dedupe by provider/source event keys |
| Calibration collector state | `data/collector_scheduler` | `raw_prediction_markets`, `settlements`, `model_predictions` | Runtime control-plane table should be separate from market warehouse | 10K8/10K9 | Do not start prediction testing |
| Experiment history | `experiment_history_runs` | `backtest_runs`, `performance_metrics` | Run configuration details may need artifact pointer | 10K6 | Current table is caller-supplied SQLite |
| Experiment report export | Markdown download content | No direct table | Artifact storage manifest optional | 10K9 | Export artifact, not normalized fact table |
| Backtest canonical dataset | `data/backtests/canonical/latest.jsonl` | `backtest_runs`, `backtest_trades` | Dataset manifest table optional | 10K6 | Compare row counts and sample hashes before switch |
| Model predictions | Feature ablation/projection results | `model_predictions` | Stable model/run IDs required | 10K6/10K8 | Do not start prediction testing in 10K3 |
| Strategy performance | `data/strategy/performance_ledger.json` | `performance_metrics` | Strategy/run/model ID mapping | 10K6 | Keep JSON until summary parity passes |
| Equity price logs | `data/stock_log.csv` | `raw_equity_prices` | Timestamp/source metadata fields | 10K9 | Unknown active owner |
| Analysis logs | `data/analysis_log.csv` | `performance_metrics` or artifact storage | Owner and row contract unknown | 10K9 | Needs owner decision |
| Option chains | Future options data | `raw_option_chains`, `raw_option_quotes`, `features_0dte_options`, `option_backtest_trades` | Live import owner not added here | 10K4 | 0DTE work is later |
| Prediction markets | Calibration/Kalshi-like runtime candidates | `raw_prediction_markets`, `features_prediction_markets` | Source registry and settlement identity fields | 10K8 | No connector work here |
| Arbitrage candidates | Existing arbitrage modules | `arbitrage_opportunities` | Candidate schema validation later | 10K5 | No arbitrage implementation in 10K3 |
| Macro/order-book data | Future data | `raw_macro_liquidity`, `raw_order_books` | No current runtime owner validated here | 10K9 | Asset-grade cleanup happens later |

The existing `market_research.db` schema tables referenced by this plan are: `schema_metadata`, `raw_sports_odds`, `raw_equity_prices`, `raw_option_chains`, `raw_option_quotes`, `raw_prediction_markets`, `raw_macro_liquidity`, `raw_order_books`, `features_sports`, `features_equities`, `features_0dte_options`, `features_prediction_markets`, `model_predictions`, `backtest_runs`, `backtest_trades`, `option_backtest_trades`, `arbitrage_opportunities`, `settlements`, and `performance_metrics`.

## E. Existing Sports SQLite Preservation

Existing sports SQLite flow was not replaced.

The current sports SQLite owner remains `automation_scheduler.historical_odds_sqlite` with `data/historical/historical_odds.db` exposed through `automation_scheduler.streamlit_dashboard_data.DEFAULT_HISTORICAL_SQLITE_PATH`. The current tables are `source_imports`, `historical_events`, `historical_odds`, and `historical_results`. Line movement extends that same flow with `historical_line_snapshots`.

Preservation rules:

- Keep `data/historical/historical_odds.db` as the active historical sports store until a later phase proves warehouse parity.
- Keep `historical_line_snapshots` append-style behavior and decision-time leakage protections.
- Add mirror writes only after tests prove row shape, event identity, source metadata, and counts.
- Do not switch Feature Ablation Lab reads to `market_research.db` until old-vs-new comparison tests pass.
- Do not delete the old SQLite file or old tables during mirror phases.

## F. Duplicate Storage Owner Register

| Duplicate family | Current owners | Why it is duplicate | Decision | Deletion status |
|---|---|---|---|---|
| Bet ledger | `src.services.bet_csv_service`, `src.api.bet_csv_routes`, `bet_log.py` | `data/bets.csv` and `data/bet_log.jsonl` both represent bet lifecycle data; route also writes CSV directly | Needs owner decision, then mirror to warehouse | Tracked only |
| Runtime data root | `automation_scheduler.data_paths`, `config.py` | `get_runtime_data_path` uses configured runtime root while `config.py` has legacy `data/...` strings | Keep `data_paths`; validate config usage later | Tracked only |
| Sports odds store | `historical_odds_sqlite`, `research.market_research_store` | Existing sports SQLite overlaps future `raw_sports_odds` | Keep SQLite; mirror later | Tracked only |
| Line movement snapshots | `historical_line_movement`, future warehouse raw sports schema | Snapshot history can be represented as raw odds rows or a dedicated table | Needs schema decision | Tracked only |
| Paper ledgers | `paper_trade_ledger`, `paper_decision_ledger`, scheduler/calibration persistence | Multiple JSON files under `paper_ledger` describe similar paper decision/trade lifecycle | Migrate later | Candidate for deletion after migration tests |
| Outcomes | `outcome_store`, paper ledgers, bet log updates | Settlement outcome appears in multiple owners | Migrate later with ID reconciliation | Candidate for deletion after migration tests |
| Experiment performance | `experiment_history_store`, `strategy_performance_ledger`, `model_performance_report`, backtest artifacts | Run metrics are stored in several runtime formats | Migrate later | Tracked only |
| Source metadata | `historical_odds_sqlite.source_imports`, `data_source_registry`, open sports import reports | Source metadata appears in SQLite and registry/report artifacts | Needs source registry table decision | Tracked only |
| Dashboard artifacts | `streamlit_dashboard_data`, backtest dataset builder, report writer | Dashboard JSON/MD and canonical JSONL are derived artifacts | Export artifact | Tracked only |

Duplicate storage owners are tracked, not deleted.

## G. Staged Migration Plan

Staged Migration Plan:

1. Inventory current stores and source owners.
2. Validate active wiring by reading source and existing tests.
3. Add warehouse write path behind explicit tests.
4. Mirror writes before switching reads.
5. Compare old vs warehouse rows.
6. Keep old reads active until parity checks pass.
7. Switch reads only after row-count, ID, timestamp, summary, and sample-hash parity is proven.
8. Mark old files as Candidate for deletion after migration tests.
9. Delete only in a later cleanup phase after user approval and green tests.

Mirror writes before switching reads is the key rule. Compare old vs warehouse rows before any read switch. Candidate for deletion after migration tests means a path is only a later candidate, not removed in 10K3.

Minimum comparison checks for later phases:

- Row counts by source owner and date.
- Stable IDs and dedupe keys.
- Required field presence and null rates.
- Timestamp ordering and append-only behavior.
- Summary parity for wins/losses/ROI/settlements/performance.
- Sample record hash parity after canonical normalization.
- Read-path fallback behavior when warehouse is empty.

## H. No-Deletion Rule

No runtime files were deleted.

No CSV paths were deleted.

No migration was executed in this phase.

Duplicate storage owners are tracked, not deleted.

This phase does not remove `bets.csv`, `bet_log.jsonl`, runtime JSON files, generated dashboard artifacts, `data/historical/historical_odds.db`, or any sports SQLite tables. Even paths marked Candidate for deletion after migration tests remain untouched until a later phase proves parity and receives explicit cleanup approval.

## I. Test Plan

Efficient same-flow tests for this phase:

- `pytest tests/test_phase10k3_runtime_csv_migration_plan.py`
- `pytest tests/test_market_research_store.py`
- `pytest tests/test_data_paths.py`
- `pytest tests/test_historical_odds_sqlite.py tests/test_historical_line_movement.py`
- `pytest tests/test_bet_log.py tests/test_paper_trade_ledger.py tests/test_paper_decision_ledger.py tests/test_outcome_store.py`
- `pytest tests/test_streamlit_dashboard_data.py tests/test_feature_ablation_lab.py`

The new 10K3 tests validate that the report exists, all required report strings and sections are present, the Streamlit main menu remains exactly protected, the runtime and CSV owners remain source-backed, `market_research.db` target tables initialize in a temporary database, the existing sports SQLite flow remains present, duplicate owners are documented, and forbidden overreach claims are absent.

Do not add vendor connectors. Do not start prediction testing. Do not alter Streamlit main menu. Do not run data migration scripts in this phase.

## J. Next Phase Impact

Phase 10K4 0DTE: use `raw_option_chains`, `raw_option_quotes`, `features_0dte_options`, and `option_backtest_trades`; do not infer options storage from legacy stock CSVs.

Phase 10K5 arbitrage: use `arbitrage_opportunities` only after source identity and timing rules are validated; no arbitrage execution is introduced by this phase.

Phase 10K6 frontend/readiness: keep Feature Ablation Lab reads on existing SQLite until mirror and comparison tests pass; menu remains Feature Ablation Lab, Bankroll Settings, Instructions.

Phase 10K8 prediction testing: prediction market runtime files and collector state must be mapped deliberately to `raw_prediction_markets`, `features_prediction_markets`, `model_predictions`, and `settlements`; Do not start prediction testing in 10K3.

Phase 10K9 asset-grade clean product repo: consolidate duplicate owners only after migration parity, read-switch tests, deletion-candidate review, and explicit cleanup approval. Asset-grade cleanup happens later.
