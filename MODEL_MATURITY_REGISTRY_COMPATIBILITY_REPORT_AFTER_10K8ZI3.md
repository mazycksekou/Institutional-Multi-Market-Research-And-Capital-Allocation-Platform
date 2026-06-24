# Model Maturity Registry Compatibility Report After 10K8ZI3

- `src.research.maturity` owns the registry logic.
- `automation_scheduler.model_maturity_registry` remains a compatibility shim only.
- `automation_scheduler.data_intelligence_registry` and
  `automation_scheduler.cross_asset_intelligence_router` use the canonical owner.
- No scheduler activation or credential access is introduced.
