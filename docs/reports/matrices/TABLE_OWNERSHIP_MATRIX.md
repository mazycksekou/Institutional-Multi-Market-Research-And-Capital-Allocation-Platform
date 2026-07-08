
# Table Ownership Matrix

| Table family | Planned owner | Read/write policy | Notes |
| --- | --- | --- | --- |
| `dataset_registry` | `src.data` | read/write | Canonical registry for all datasets. |
| `dataset_versions` | `src.data` | read/write | Version history and compatibility. |
| `raw_records` | `src.data` | write-once | Immutable raw acquisition cache payloads. |
| `normalized_records` | `src.data` | write-once per version | Canonical normalized data. |
| `feature_snapshots` | `src.data` / `src.market_intelligence` | read/write | Feature materialization is owned by the data platform, computed by domain code. |
| `lineage_edges` | `src.data` | append-only | Provenance graph. |
| `validation_results` | `src.data` | append-only | Validation outcomes and warnings. |
| `provider_metadata` | `src.providers` | read/write | Provider mappings and contracts. |
| `model_runs` | `src.analytics` | append-only | Evaluation and calibration registry. |
| `backtest_runs` | `src.backtesting` | append-only | Backtest execution registry. |
| `research_runs` | `src.research` | append-only | Experiments and studies. |
| `streamlit_layouts` | `src.services` | versioned write | Dashboard layout metadata. |
| `audit_events` | `src.services` / `src.data` | append-only | Audit trail and operational trace. |

## Ownership Rule

Each row has one canonical owner for persistence semantics. Domain packages may contribute computed content, but the storage contract itself is owned by the data platform.
