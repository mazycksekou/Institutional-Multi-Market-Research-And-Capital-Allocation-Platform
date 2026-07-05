# PHASE10K8ZI6 AI/LLM Boundary Audit

This phase inventories AI/LLM and model-call-adjacent surfaces and maps them to a future `src.ai` boundary.

Canonical target:
- `src.ai` owns boundary contracts, prompt policy, disabled clients, readiness, and evaluation metadata.

Deferred domains:
- AI/LLM execution remains deferred.
- Brokerage/live execution remains deferred.
- Production activation remains deferred.

Key findings:
- `automation_scheduler/deepseek_reviewer.py` and related DeepSeek modules contain runtime call risk.
- `automation_scheduler/ai_provider_security.py`, `automation_scheduler/advanced_red_team_provider_policy.py`, `config.py`, and `src/providers/policy/secret_policy.py` contain credential-policy risk.
- `src/api/automation_deepseek_routes.py` is `MIGRATE_TO_SRC_AI_LATER`.
- `src/api/automation_deepseek_routes.py` and `main.py` expose AI-adjacent runtime wiring and should remain deferred to a later service-thinning phase.
- `deepseek_prompt_contracts.py` is prompt-template only and can safely inform the disabled boundary.
- `src.ai` is scaffolded as an inert package only; it does not call models or read secrets at import time.

No AI call is enabled by this audit.
