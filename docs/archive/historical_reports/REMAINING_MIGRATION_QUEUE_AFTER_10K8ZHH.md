# Remaining Migration Queue After 10K8ZHH

1. Extract screenshot workflow into `src/services/screenshot_workflow.py`.
2. Decide whether `bet_log.py` deserves a dedicated storage service or remains a root compatibility shell.
3. Continue redirecting any remaining scheduler orchestration into `src.services`.
4. Thin `src/api/provider_status_routes.py` away from `automation_scheduler`.
5. Keep dashboard/bootstrap files thin and untouched for now.
6. Keep AI/LLM deferred until canonical data and evaluation layers are complete.
7. Keep brokerage/live execution deferred until safety and execution layers are in place.
