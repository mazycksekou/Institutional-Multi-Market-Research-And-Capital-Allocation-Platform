# PHASE10K8ZI3 Model Maturity Registry Decoupling

Canonical model maturity ownership now lives in `src.research.maturity`.
Scheduler-facing registry helpers are redirected to the canonical research package.

`automation_scheduler/model_maturity_registry.py` is a scheduler-facing compatibility shim once
all runtime consumers and tests use the canonical path.

No scheduler activation, AI/LLM, or live behavior is introduced.
