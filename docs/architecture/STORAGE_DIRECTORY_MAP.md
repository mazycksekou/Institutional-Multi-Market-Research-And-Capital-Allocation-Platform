
# Storage Directory Map

## Canonical Layout

The storage hierarchy is market-agnostic and version-aware.

| Layer | Canonical path | Purpose | Notes |
| --- | --- | --- | --- |
| Raw Data | `data/raw/` | Immutable source payloads exactly as imported. | Partition by provider, market, asset class, and schema version. |
| Normalized Data | `data/normalized/` | Canonical records after validation and field normalization. | This is the preferred read path for downstream consumers. |
| Feature Store | `data/features/` | Materialized feature outputs. | Store feature pack version and snapshot lineage. |
| Historical Snapshots | `data/snapshots/` | Point-in-time captures for reproducibility. | Use for replays and auditability. |
| Backtests | `data/backtests/` | Backtest inputs, outputs, and run metadata. | Must preserve leakage checks and version tags. |
| Paper Trading | `data/paper_trading/` | Paper-trading state and simulation outputs. | Read/write separated from raw source data. |
| Calibration | `data/calibration/` | Calibration curves, thresholds, and evaluation artifacts. | Versioned by model and feature-pack release. |
| Model Registry | `data/models/` | Trained model artifacts and registry metadata. | No anonymous model blobs. |
| Research | `data/research/` | Experiments, studies, and evaluation outputs. | Organize by project and experiment id. |
| Provider Metadata | `data/providers/` | Provider contracts, mappings, and health summaries. | Read-only to ingestion workers. |
| Health | `data/health/` | Data platform health snapshots. | Includes validation and freshness checks. |
| Audit Logs | `data/audit/` | Immutable audit trails. | Append-only. |
| Reports | `data/reports/` | Machine-generated runtime reports. | Distinct from documentation in `docs/reports/`. |
| Experiment History | `data/experiments/` | Historical experiment summaries and lineage. | Can be mirrored into `data/research/`. |
| Temporary Cache | `data/cache/` | Short-lived working cache. | TTL-managed and safe to purge. |
| Archives | `archives/` | Long-term historical snapshots and retained artifacts. | Prefer archive over delete for audit evidence. |

## Partition Rule

Do not hardcode market-specific paths. Use partitions such as:

- `market=<market>`
- `market_type=<market_type>`
- `asset_class=<asset_class>`
- `provider=<provider>`
- `schema_version=<n>`
- `version_id=<id>`
- `snapshot_id=<id>`

## Current Repository Note

The repo already uses a local `data/` fallback in ops checks when `AUTOMATION_DATA_DIR` is unset. This map formalizes that behavior into a stable layer model.
