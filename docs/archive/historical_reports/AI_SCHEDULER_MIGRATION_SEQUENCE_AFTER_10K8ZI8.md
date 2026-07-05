# AI Scheduler Migration Sequence After 10K8ZI8

1. Keep `src.ai` disabled and import-safe.
2. Move only local prompt-policy and readiness metadata into `src.ai`.
3. Reclassify red-team and embedding metadata into `src.research` or `src.analytics` later.
4. Keep `automation_scheduler/deepseek_*` and `src/api/automation_deepseek_routes.py` deferred until service ownership is proven.
5. Do not activate any AI/LLM call paths in scheduler code.

