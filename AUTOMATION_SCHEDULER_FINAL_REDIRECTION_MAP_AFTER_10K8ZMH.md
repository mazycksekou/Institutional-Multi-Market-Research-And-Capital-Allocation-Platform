# Automation Scheduler Final Redirection Map After 10K8ZMH

No runtime redirections were needed in this batch because runtime imports are already at zero.

Canonical destination families already in place:
- `market intelligence / sports / prediction / manifold` -> `src.market_intelligence`
- `data / historical odds / line movement` -> `src.data`
- `backtesting / replay / strategy profiles` -> `src.backtesting`
- `research / feature control / experiment history` -> `src.research`
- `dashboards / workflow / facades` -> `src.services` or `src.analytics`
- `brokerage readiness / execution / ledger / settlement` -> `src.brokerage` or `src.services`
- `disabled AI-only surfaces` -> `src.ai`

Canonical modules verified as safe to import in this phase:
- `src.services.streamlit_dashboard_facade`
- `src.services.automation_scheduler_facade`
- `src.market_intelligence.manifold`
- `src.data.historical_odds`
- `src.backtesting.engine`
- `src.research.history`
- `src.services.runtime_shared`
- `src.analytics.performance`
- `src.brokerage.readiness`
- `src.ai.readiness`

Result:
- The runtime bridge is canonical.
- The remaining migration work is the relocated legacy namespace, not the deleted top-level package.
