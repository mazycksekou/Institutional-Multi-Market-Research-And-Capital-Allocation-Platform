# Feature Pipeline Graph

```mermaid
graph TD
    A["Providers / CSV / SQLite / Parquet / Manual import"] --> B["src.data normalized contracts"]
    B --> C["src.market_intelligence feature construction"]
    C --> D["src.backtesting snapshots and leakage checks"]
    D --> E["src.analytics summaries / governance / reporting"]
    D --> F["src.services dashboard and facades"]
    C --> G["src.research experiments / calibration"]
    B --> H["src.providers contracts / registry / routing"]
```

## Pipeline summary

- Raw source candidates land in `src.data`.
- Canonical feature construction happens in `src.market_intelligence`.
- Leakage-safe snapshots and simulations happen in `src.backtesting`.
- Readiness and governance summaries land in `src.analytics` and `src.services`.
- Research and ablation remain separate from operational models.
