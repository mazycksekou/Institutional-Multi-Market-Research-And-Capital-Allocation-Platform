# AI Disabled Behavior After 10K8ZI7

The AI boundary is inert.

Disabled client methods:
- `complete()`
- `chat()`
- `generate()`
- `embed()`
- `invoke()`
- `run()`
- `__call__()`

Each method raises `AIExecutionDisabledError`.

The readiness helper returns:
- `status = deferred`
- `enabled = False`
- `local_only = True`
- no external call authority

