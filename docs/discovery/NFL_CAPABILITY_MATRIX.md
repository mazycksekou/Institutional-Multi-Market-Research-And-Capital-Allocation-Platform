# NFL Capability Matrix

This matrix classifies the current repository NFL surface by capability rather than by implementation file alone.

Legend:

- `canonical` = a real ownership boundary exists and the repo already treats it as the current source of truth
- `partial` = real capability exists, but the end-to-end slice is incomplete
- `scaffold` = the contract or helper exists, but it is not backed by a fully usable pipeline yet
- `placeholder` = intentionally blocked, metadata-only, or future-facing
- `duplicate` = redundant with another surface
- `deprecated` = kept only for compatibility / transition reasons
- `missing` = no meaningful capability was found
- `unknown` = not proven by discovery

| Capability | Status | Evidence | Notes |
|---|---|---|---|
| NFL open-data source registry | partial | `src/data/nfl_open_data_sources.py`, `docs/reports/matrices/SPORT_CAPABILITY_MATRIX.md` | Strong discovery catalog, but not validated ingest. |
| NFL open-data field catalog | partial | `src/data/nfl_open_data_field_catalog.py` | 188 catalogued fields, 0 verified fields in the discovery pass. |
| NFL source exhaustion audit | canonical | `src/data/nfl_open_data_source_exhaustion.py` | Metadata-only audit, no provider activation. |
| NFL feature-builder readiness | partial | `src/providers/nfl_open_data_feature_builders.py`, `src/providers/nfl_open_data_feature_readiness.py` | Builders are present, but blocked by no validated records. |
| NFL coaching source registry | partial | `src/market_intelligence/nfl_coaching_sources.py` | Sources are catalogued; most are blocked by terms/robots/provenance. |
| NFL coaching feature builders | partial | `src/market_intelligence/nfl_coaching_feature_builders.py` | Feature contracts exist, but data is unavailable. |
| Point-in-time cutoff-week helpers | partial | `src/market_intelligence/nfl_cutoff_week_features.py` | Leakage controls exist as contracts and helpers. |
| Historical pattern lab | partial | `src/data/nfl_historical_pattern_lab.py` | Pattern and similarity catalog exist; expanded feature catalog is not yet available. |
| Football impact diagnostics | partial | `src/analytics/football_impact_report.py` | Diagnostic and readiness surfaces exist, but tier-0 is still the default. |
| Football calibration / red-team checks | partial | `src/analytics/football_impact_calibration.py`, `src/analytics/football_impact_red_team.py` | Calibrators exist, but real settled-outcome evidence is still missing. |
| Dashboard / Streamlit NFL surfaces | partial | `src/services/streamlit_dashboard_facade.py`, `streamlit_app.py` | UI support is present through facades and report renderers. |
| NFL API surface | partial | `main.py`, `src/api/*` routes, response compactors | Shared API layer exposes football diagnostics, not a dedicated NFL router. |
| Backtesting support | scaffold | `src/backtesting/*`, `docs/contracts/NFL_BACKTEST_CONTRACT.md` (to be created) | Backtest contracts can be designed now, but the data slice is not complete. |
| Model interface support | scaffold | `src/analytics/football_impact_*`, `tests/test_nfl_model_activation.py` | Model-ready APIs exist, but there is no full NFL model pipeline yet. |
| Storage / lineage support | partial | `src/data/*`, existing data contracts, `src/data/historical_odds*` | Data contracts and local storage patterns exist, but NFL-specific lineage is not fully end-to-end. |
| Validation support | partial | `scripts/ops_check.py`, current test suite, existing governance docs | Governance is strong; NFL data validation still needs the final slice. |
| Provider activation | missing | discovery found blocked or disabled lanes only | No NFL provider activation was performed in this phase. |
| Live execution | missing | not present in NFL discovery outputs | Explicitly out of scope for this phase. |

## Practical Reading

- The repo has real NFL architecture, not a blank scaffold.
- The NFL slice is still incomplete at the data-availability layer.
- The strongest current owners are the open-data registry, feature readiness helpers, coaching registry, and football impact diagnostics.
- The weakest area is validated point-in-time NFL data availability suitable for reproducible backtesting.

