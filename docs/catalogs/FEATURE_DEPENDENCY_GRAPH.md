# Feature Dependency Graph

```mermaid
graph LR
    raw["Raw input metrics"] --> data["src.data"]
    data --> mi["src.market_intelligence"]
    mi --> bt["src.backtesting"]
    bt --> an["src.analytics"]
    bt --> svc["src.services"]
    mi --> research["src.research"]
    data --> providers["src.providers"]
    svc --> api["src.api / streamlit_app.py"]
```

## Dependency notes

- `src.data.model_data_field_catalog` is the canonical catalog for model inputs and output metrics.
- `src.market_intelligence.feature_packs` is the canonical catalog for sport and market pack definitions.
- `src.services.streamlit_dashboard_data` is the canonical dashboard contract for feature visibility.
- `src.backtesting.backtest_schema` is the canonical leakage-safe boundary.
