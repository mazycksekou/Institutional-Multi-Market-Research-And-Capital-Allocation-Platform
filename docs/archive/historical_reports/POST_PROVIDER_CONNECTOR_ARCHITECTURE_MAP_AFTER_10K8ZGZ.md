# Post‑Provider/Connector Architecture Map (After 10K8ZGZ)

## Component Layers

```
[External Data Source]
    |
    v
src/connectors/    (disabled live transport, status, readiness)
    |
    v
src/providers/    (normalised product data, read‑only snapshots)
    |
    v
src/services/     (orchestration bridges, enrichment, decision flow)
    |
    v
src/core/         (stateless math, probability, pricing, risk, execution)
    |
    v
automation_scheduler/   (decommission target – legacy workflow)
```

## Active Canonical Flows

1. **Odds** – disabled, no live API calls. Read‑only readiness.
2. **Prediction Markets** – disabled, no live API calls. Read‑only readiness.
3. **Market Data / Zero‑DTE Stocks** – disabled, no live API calls. Read‑only readiness.

## Ownership Boundaries

- `src/connectors/` – raw external data access, auth metadata, disabled transport.
- `src/providers/` – normalised product records, categories, routing.
- `src/services/` – orchestration, enrichment, dashboard data, decision flow.
- `src/core/` – math, probability, pricing, risk, portfolio, execution, game theory.
- `main.py`, `streamlit_app.py` – entrypoint / dashboard shells.
- `automation_scheduler/` – legacy, not to receive new ownership.
