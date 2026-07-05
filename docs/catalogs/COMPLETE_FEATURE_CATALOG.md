# Complete Feature Catalog

## Canonical feature families

| Family | Canonical owner | Shape |
|---|---|---|
| Universal field groups | `src.services.streamlit_dashboard_data` | `core_event(5)`, `line_core(6)`, `line_movement(8)`, `settlement(5)`, `team_stats(7)`, `player_stats(8)`, `projection_control(2)` |
| Sport feature packs | `src.market_intelligence.feature_packs` | 43 packs across full/thin/fallback depth |
| Market feature packs | `src.market_intelligence.feature_packs` | 57 packs across full/standard/thin/fallback depth |
| Model field catalog modes | `src.data.model_data_field_catalog` | `one_sport=162`, `one_stock_market=188`, `one_crypto_market=160`, `one_prediction_market=149`, `one_0dte_options_trade=189` |
| Output metric families | `src.data.model_data_field_catalog` | `Sports=25`, `Stocks / 0DTE=21`, `Predictions=19` |

## Dashboard feature-control catalog

| Profile | Meaning |
|---|---|
| Available Baseline | Use the fields we currently have without pretending missing fields exist |
| Odds Only | Test market/odds fields only |
| Remove Line Movement | Ignore line movement fields when not available |
| Settlement Check | Focus on whether outcomes/results exist |
| Custom Add/Remove | Operator chooses included/excluded fields |

## Why this matters

The repo already separates feature groups known at decision time, never-feature leakage fields, market output metrics, backtest validation metrics, and dashboard display contracts.
