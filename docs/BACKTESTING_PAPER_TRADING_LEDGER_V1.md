# Backtesting + Paper Trading Ledger v1

## Scope
- Dry-run only (`dry_run=true`)
- Paper tracking only (`paper_execution_only=true`)
- Human approval required (`human_approval_required=true`)
- No auto execution (`auto_bet_enabled=false`, `auto_trade_enabled=false`, `auto_execution_enabled=false`)
- Local JSON storage only

## Storage Paths
- `data/backtests/`
- `data/paper_ledger/`
- `data/clv/`
- `data/performance_reports/`
- `data/calibration/`

Directories are created at runtime by the corresponding modules.

## Components
- `automation_scheduler/paper_trade_ledger.py`:
  - Writes and updates paper-only recommendations.
  - Settles entries into win/loss/push states.
  - Produces compact ledger summaries.
- `automation_scheduler/clv_tracker.py`:
  - Computes CLV from American odds and implied probabilities.
  - Tracks positive CLV rate and CLV decay.
- `automation_scheduler/performance_metrics.py`:
  - Computes observed ROI, expected ROI, profit factor, hit rate, and max drawdown.
  - Emits sample-size warnings and a CI placeholder.
- `automation_scheduler/calibration_tracker.py`:
  - Buckets probabilities from `0.50-0.55` up to `0.75+`.
  - Computes Brier score, log loss, ECE, and overconfidence detection.
- `automation_scheduler/historical_replay.py`:
  - Loads local historical rows and replays into dry-run records.
  - Writes replay artifacts under `data/backtests/`.
- `automation_scheduler/backtesting_engine.py`:
  - Coordinates replay, CLV, performance, and calibration metrics.
  - Produces compact and full performance reports.
- `automation_scheduler/model_performance_report.py`:
  - Persists full internal report payloads.
  - Returns compact report payloads for API responses.

## API Endpoints
- `GET /api/performance/health`
- `GET /api/performance/report`
- `POST /api/performance/backtest`
- `POST /api/performance/paper-summary`

Endpoint behavior:
- Analysis only.
- Compact by default.
- Verbose detail only when `verbose=true` or `include_debug=true`.
- No full ledger or full replay rows in default response.

## Governance + Health Integration
- Backtest and calibration gates accept and emit performance-aware status fields.
- Validation report supports `paper_tracking_summary` and `clv_summary`.
- Governance health includes:
  - `backtest_ready_count`
  - `blocked_by_performance_count`
  - `blocked_by_calibration_count`
- System health includes:
  - `paper_ledger_count`
  - `settled_paper_count`
  - `clv_sample_size`
  - `latest_performance_report_id`
  - `models_with_positive_clv`
  - `models_needing_revalidation`
