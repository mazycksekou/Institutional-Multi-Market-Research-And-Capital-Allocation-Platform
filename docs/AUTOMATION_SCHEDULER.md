# Automation Scheduler v1

`automation_scheduler` is a dry-run, local-only monitoring subsystem for sportsbook odds, player props, prediction markets, stocks, news/event changes, model rechecks, review queues, reports, and system health.

## Safety Defaults

- `dry_run = true`
- `human_approval_required = true`
- `auto_bet_enabled = false`
- `auto_trade_enabled = false`
- `auto_execution_enabled = false`
- `paper_execution_only = true`
- `alert_only_mode = true`

## Local Storage

All runtime artifacts are written under `data/`:

- `data/snapshots/`
- `data/reports/`
- `data/review_queue/`
- `data/audit_log/`
- `data/system_health/`

Directories are created automatically at runtime.

## Competitive Cadence Profiles

- `sports_pregame_main`: `30s / 60s / 300s`
- `sports_player_props`: `45s / 90s / 300s`
- `sports_live`: streaming preferred, `5s / 15s / 60s fallback`, not competitive if provider cannot stream
- `prediction_markets`: streaming preferred, `15s / 30s / 300s`
- `stocks_watchlist`: streaming preferred, `5s / 15s / 60s`
- `stocks_broad`: `60s / 300s`
- `news_events`: `60s / 300s / 900s`
- `low_liquidity`: `300s / 900s`

## Scoring

Field scorecard outputs `0-10` scores for:

- `edge_score`
- `confidence_score`
- `liquidity_score`
- `movement_score`
- `data_quality_score`
- `market_depth_score`
- `timing_score`
- `model_fit_score`
- `risk_score`
- `volatility_score`
- `source_consensus_score`
- `execution_feasibility_score`
- `expected_roi_score`

`opportunity_score` is combined into `0-100`.

Thresholds:

- ignore below `55`
- watch `55-69`
- review `70-84`
- urgent `85+`
- later auto-execution threshold `92`

## Review Queue

Items remain active until one of the following occurs:

- market close
- stale data
- human rejection
- score decay below threshold

All actionable items require human approval.

## Safe Endpoints

- `GET /api/automation/health`
- `GET /api/automation/review-queue`
- `POST /api/automation/run-once`

`run-once` is dry-run only and does not call external providers.

## Reporting

Reports are JSON only. Every report includes:

`ROI target is a filter target, not a guarantee.`

## Cross-Book Engine

The scheduler also supports evaluation-only cross-book analysis for:

- positive EV
- best-line shopping
- no-vig and consensus EV
- arbitrage candidates
- middle candidates
- CLV watch records

This engine is dry-run only and never places bets or trades.

## Institutional Model Library

The repository also includes a separate `math_models.institutional` library for:

- portfolio construction
- factor and credit risk
- liability and retirement planning
- fixed-income and derivatives analytics
- execution cost analysis
- alternatives, macro regime, tax-aware, attribution, and governance models

These models default to `research_only`. They are metadata-first and gated by evidence, input quality, model risk, time horizon, and market relevance before any review-queue field can be populated.
