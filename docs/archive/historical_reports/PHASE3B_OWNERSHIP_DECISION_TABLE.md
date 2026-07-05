# Phase 3B Ownership Decision Table

Scope note:
- This table is the pre-implementation ownership map for the local data platform.
- Existing working odds, line-movement, dashboard, backtest, lineage, validation, provider, and path helpers are reused wherever they already satisfy the responsibility.
- New code is permitted only where a responsibility is not currently owned by a reusable module.

| responsibility | existing module found | current owner | reuse decision | canonical target | action | reason |
|---|---|---|---|---|---|---|
| historical odds store | `src.data.historical_odds_sqlite`, `src.data.historical_odds` | `src.data` | KEEP_AS_CANONICAL | `src.data.historical_odds_sqlite` | WRAP_EXISTING | Existing SQLite odds store already owns validated historical-odds persistence and import helpers. |
| line movement store | `src.data.line_movement`, `src.data.historical_line_movement` | `src.data` | KEEP_AS_CANONICAL | `src.data.line_movement` | WRAP_EXISTING | Existing line-movement store already owns line snapshots, readiness, and query helpers. |
| dashboard data adapters | `src.services.streamlit_dashboard_data` | `src.services` | KEEP_AS_CANONICAL | `src.services.streamlit_dashboard_data` | WRAP_EXISTING | Existing dashboard data layer already composes historical odds, line movement, backtest, and readiness helpers. |
| dashboard compatibility facade | `src.services.streamlit_dashboard_facade` | `src.services` | WRAP_EXISTING | `src.services.streamlit_dashboard_facade` | WRAP_EXISTING | Facade is an intentional compatibility surface, not a business-logic owner. |
| lineage helpers | `src.analytics.model_governance.data_lineage` | `src.analytics.model_governance` | KEEP_AS_CANONICAL | `src.analytics.model_governance.data_lineage` | WRAP_EXISTING | Current lineage helper is already used by runtime code and redacts sensitive fields safely. |
| validation helpers | `src.data.validation` | `src.data` | KEEP_AS_CANONICAL | `src.data.validation` | WRAP_EXISTING | Existing validation helpers are reusable and already import-safe. |
| dataset metadata helpers | `src.data.metadata`, `src.data.contracts` | `src.data` | KEEP_AS_CANONICAL | `src.data.metadata` | WRAP_EXISTING | Existing dataset metadata constructors and descriptors already cover local-only metadata needs. |
| provider metadata helpers | `src.providers.contracts`, `src.providers.registry` | `src.providers` | KEEP_AS_CANONICAL | `src.providers.contracts` | WRAP_EXISTING | Provider metadata ownership already lives in providers and should not be duplicated by the data platform. |
| feature-pack helpers | `src.market_intelligence.feature_packs` | `src.market_intelligence` | KEEP_AS_CANONICAL | `src.market_intelligence.feature_packs` | WRAP_EXISTING | Feature-pack helpers already own field-group discovery and readiness summaries. |
| source quality helpers | `src.data.source_quality_scoring` | `src.data` | KEEP_AS_CANONICAL | `src.data.source_quality_scoring` | WRAP_EXISTING | Source quality scoring already owns source scoring and safety tier logic. |
| local data path helpers | `src.data.data_paths` | `src.data` | KEEP_AS_CANONICAL | `src.data.data_paths` | WRAP_EXISTING | Local path ownership already exists and is reused by multiple runtime helpers. |
| backtest storage helpers | `src.backtesting.dataset_builder`, `src.backtesting.historical_bridge`, `src.backtesting.engine` | `src.backtesting` | KEEP_AS_CANONICAL | `src.backtesting.dataset_builder` | WRAP_EXISTING | Backtesting persistence and conversion helpers already exist and should be reused, not recreated. |
| model governance helpers | `src.analytics.model_governance` | `src.analytics.model_governance` | KEEP_AS_CANONICAL | `src.analytics.model_governance` | WRAP_EXISTING | Governance helper namespace already owns lineage-style record shaping and validation patterns. |
| storage backend abstraction | no canonical module found | none | MISSING | `src.storage.local_store` | CREATE_NEW_ONLY_IF_MISSING | No generic local storage engine exists yet for SQLite/DuckDB-backed canonical tables. |
| dataset registry persistence | no canonical module found | none | MISSING | `src.data.local_platform` | CREATE_NEW_ONLY_IF_MISSING | No canonical dataset registry exists for register/read/update/deprecate/version flows. |
| lineage persistence / trace | no canonical module found | none | MISSING | `src.data.local_platform` | CREATE_NEW_ONLY_IF_MISSING | Existing lineage helper creates records, but the platform still lacks persistent lineage edges and trace summaries. |
| versioning store | no canonical module found | none | MISSING | `src.data.local_platform` | CREATE_NEW_ONLY_IF_MISSING | No dataset/version registry exists for version history and reproducible dataset snapshots. |
| feature snapshot store | no canonical module found | none | MISSING | `src.data.local_platform` | CREATE_NEW_ONLY_IF_MISSING | No canonical feature snapshot persistence exists yet. |
| synthetic fixture proof | no canonical module found | none | MISSING | `src.data.local_platform` | CREATE_NEW_ONLY_IF_MISSING | A single deterministic synthetic dataset is needed to prove ingest/validate/store/read-back. |
| local dashboard proof snapshot | `src.services.streamlit_dashboard_data` | `src.services` | WRAP_EXISTING | `src.services.streamlit_dashboard_data` | WRAP_EXISTING | The dashboard proof should be added as a thin adapter over the existing dashboard data layer. |

Implementation constraint:
- Do not create any new canonical module unless the responsibility is marked `MISSING`.
- Do not duplicate the existing odds, line-movement, dashboard, backtest, provider, or validation owners.
