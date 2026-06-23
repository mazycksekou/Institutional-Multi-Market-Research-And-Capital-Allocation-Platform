# Service Layer Thinning Sequence After 10K8ZHB

1. Keep `src/services/decision_engine.py` as the canonical decision orchestration owner.
2. Keep `src/services/enrichment_service.py` as the canonical enrichment orchestration owner.
3. Move screenshot workflow implementation from `screenshot_intake.py` into `src/services/screenshot_workflow.py`.
4. Keep `bet_log.py` as a root-level compatibility/storage shell until a storage-service plan exists.
5. Keep `bet_decision_engine.py` as a compatibility shell until callers are redirected.
6. Preserve `src/services/odds_runtime_bridge.py` and `src/services/prediction_market_runtime_bridge.py` as canonical bridge layers.
7. Redirect any remaining `automation_scheduler` orchestration into `src/services` only after proof and import safety are established.

## Deferred Domains

- AI/LLM remains deferred.
- Brokerage/live execution remains deferred.
- Live production activation remains deferred.
