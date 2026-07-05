# Feature Ownership Matrix

| Feature family | Canonical owner | Consumers | Storage / contract |
|---|---|---|---|
| Core event | `src.data` + `src.market_intelligence` | model input contracts, dashboard, backtests | `REQUIRED_FIELD_GROUPS.core_event` |
| Line core | `src.data` + `src.market_intelligence` | pricing, signal generation, dashboard | `REQUIRED_FIELD_GROUPS.line_core` |
| Line movement | `src.data.line_movement` + `src.backtesting` | historical replay, readiness, streamlit | `REQUIRED_FIELD_GROUPS.line_movement` |
| Settlement | `src.data` + `src.backtesting` | leakage checks, outcome validation | `REQUIRED_FIELD_GROUPS.settlement` |
| Team stats | `src.market_intelligence` | sports models and dashboard | `REQUIRED_FIELD_GROUPS.team_stats` |
| Player stats | `src.market_intelligence` | props and sports models | `REQUIRED_FIELD_GROUPS.player_stats` |
| Projection control | `src.core` + `src.backtesting` | leakage-safe model evaluation | `REQUIRED_FIELD_GROUPS.projection_control` |
| Technical signal fields | `src.market_intelligence` | model input catalog and signal generation | `src.data.model_data_field_catalog` |
| Output metrics | `src.analytics` | reports, dashboards, scorecards | `src.data.model_data_field_catalog.output_metrics_for_product_lane` |
| Feature control profiles | `src.services` + `src.research` | dashboard feature control lab | `src.services.streamlit_dashboard_data` |
