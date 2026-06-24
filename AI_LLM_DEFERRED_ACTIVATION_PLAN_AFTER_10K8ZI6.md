# AI/LLM Deferred Activation Plan After 10K8ZI6

1. Keep `src.ai` as the canonical disabled boundary.
2. Use `src.ai.prompt_policy` for local-only prompt metadata validation.
3. Use `src.ai.disabled_client` for all future no-op AI client shells.
4. Move only deterministic AI-related metadata into `src.ai` or `src.research`.
5. Leave `automation_scheduler/deepseek_*` and `src/api/automation_deepseek_routes.py` untouched until a separate service-thinning proof exists.
6. Do not enable any live model calls, embeddings, prompt execution, or scheduler-triggered AI behavior in this phase.

