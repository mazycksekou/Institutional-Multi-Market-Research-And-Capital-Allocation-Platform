
# Data Provenance Map

| Stage | Stored artifact | Required provenance fields |
| --- | --- | --- |
| Raw source | Raw payload record | `source`, `provider`, `snapshot_id`, `schema_version` |
| Normalized source | Normalized dataset row | `lineage_id`, `market`, `market_type`, `asset_class` |
| Feature generation | Feature snapshot | `version_id`, `feature_pack`, `quality_score` |
| Model usage | Model input batch | `model_version`, `feature_pack_version`, `snapshot_id` |
| Backtest usage | Backtest input slice | `backtest_id`, `schema_version`, `lineage_id` |
| Dashboard usage | Streamlit dataset view | `layout_version`, `cache_key`, `lineage_id` |
| Paper trading usage | Paper trade record | `trade_version`, `snapshot_id`, `quality_score` |
| Research usage | Experiment artifact | `experiment_id`, `dataset_version`, `feature_pack_version` |

The provenance map is intentionally market-agnostic. Market-specific details belong in partition keys or downstream feature logic, not in the provenance contract itself.
