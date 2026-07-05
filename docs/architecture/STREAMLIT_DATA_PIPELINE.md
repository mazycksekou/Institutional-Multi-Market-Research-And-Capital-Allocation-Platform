
# Streamlit Data Pipeline

## Pipeline Goal

Streamlit should read from the canonical data platform, not from ad hoc filesystem paths.

## Current Entry Points

- `streamlit_app.py`
- `src.services.streamlit_dashboard_facade`

## Planned Page-to-Data Map

| Page | Primary datasets | Refresh strategy | Cache strategy | Owner |
| --- | --- | --- | --- | --- |
| Overview / health | provider metadata, validation results, audit logs | fast / periodic | short TTL | `src.services` + `src.data` |
| Market intelligence | feature snapshots, normalized market datasets, market state outputs | periodic | feature-level cache | `src.market_intelligence` |
| Backtests | backtest runs, performance reports, leakage checks | on-demand / periodic | keyed by backtest id | `src.backtesting` |
| Research | experiment runs, study summaries, ablation outputs | on-demand | long TTL with invalidation by version | `src.research` |
| Registry | dataset registry, model registry, provider metadata | periodic | registry cache | `src.data` |
| Ops / audit | health snapshots, audit events, provenance maps | fast | very short TTL | `src.services` |

## Design Notes

- Refresh cadence should be driven by data volatility.
- High-volatility operational views should use short-lived caches.
- Historical pages can cache longer as long as version ids are part of the cache key.
- The dashboard must not reach around the canonical data layer.
