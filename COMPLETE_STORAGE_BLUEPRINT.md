# Complete Storage Blueprint

## Layers

| Layer | Canonical location | Primary owner |
|---|---|---|
| Raw | `data/` | `src.data` + source-specific importer boundaries |
| Normalized | `data/historical/`, `data/data_sources/` | `src.data` |
| Features | feature snapshots / in-memory | `src.market_intelligence` / `src.data` |
| Models | `src/sports/models/compressed/` and model registry metadata | `src.ai` / `src.market_intelligence` |
| Research | `data/institutional_lab/` and research reports | `src.research` |
| Backtests | `data/backtests/` | `src.backtesting` |
| Reports | `data/backtests/dashboard/`, `data/calibration/` | `src.analytics` / `src.services` |
| Calibration | `data/calibration/` | `src.research` / `src.analytics` |
| Paper trades | `data/paper_ledger/` | `src.brokerage` / `src.services` |
| Logs | `data/*.log` and module-specific logs | `src.services` / platform |
| Health | `data/system_health/` | `src.services` |
| Metadata / registry | `data/data_sources/`, `data/agent_state.json`, `data/provider_cache.json` | `src.data` / `src.providers` / `src.core` |

## Canonical runtime paths discovered

| Path surface | Resolved location |
|---|---|
| Automation data root | `data/` |
| Historical odds DB | `data/historical/historical_odds.db` |
| Review queue | `data/review_queue/` |
| Paper ledger | `data/paper_ledger/` |
| Outcomes | `data/outcomes/` |
| Collector scheduler | `data/collector_scheduler/` |
| Institutional lab | `data/institutional_lab/` |
| Data sources | `data/data_sources/` |
| Calibration reports | `data/calibration/` |
| Archived model artifacts | `src/sports/models/compressed/` |

## Core path constants discovered

- `AGENT_STATE_PATH = data/agent_state.json`
- `PROVIDER_CACHE_PATH = data/provider_cache.json`
- `ALERT_LEDGER_PATH = data/alert_ledger.jsonl`
- `LIVE_AGENT_LOG_PATH = data/live_agent.log`
- `EXPOSURE_LEDGER_PATH = data/exposure_ledger.jsonl`
- `MODEL_REGISTRY_PATH = src/sports/models/compressed/model_registry.json`

## Archive constraints

- Approved archive suffixes: `.json`, `.jsonl`, `.jsonl.gz`, `.json.gz`
- Archive bundle suffixes: `.jsonl.gz`, `.json.gz`, `.tar.gz`, `.zip`
- Code suffixes are explicitly blocked from archive bundles.
