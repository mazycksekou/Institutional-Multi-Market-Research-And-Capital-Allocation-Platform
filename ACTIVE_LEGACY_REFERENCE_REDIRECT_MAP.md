# Active Legacy Reference Redirect Map

| Legacy surface | Canonical destination | Notes |
| --- | --- | --- |
| `src.providers.compat` | `src.providers.core` + `src.providers` | Provider helpers now live in `src/providers/core.py` and are exported from `src.providers`. |
| `src.services.automation_scheduler_facade` | `src.services.streamlit_dashboard_facade` | Runtime entrypoints now call the streamlit facade surface. |
| `src.market_intelligence.manifold` | `src.market_intelligence.manifold_feature_builder`, `src.market_intelligence.market_state_manifold`, `src.market_intelligence.prediction_market_manifold_mapper`, `src.analytics.manifold_review_queue`, `src.market_intelligence.cross_asset_embedding_router` | Legacy manifold consumers were redirected to canonical submodules. |
| `src.market_intelligence.manifold` test imports | Canonical `src.market_intelligence.*` modules | Stale test expectations were updated to reference the canonical owners. |

## Facade Aliases Kept

- `src.services.streamlit_dashboard_facade` keeps compatibility-oriented symbol resolution for runtime facades.
- The façade now carries type-check-only canonical bridge imports for audit text stability.
