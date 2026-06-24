# AI Boundary Ownership Map After 10K8ZI7

| Canonical file | Ownership | Notes |
| --- | --- | --- |
| `src/ai/contracts.py` | AI boundary contracts | Prompt metadata, request descriptors, readiness snapshots |
| `src/ai/prompt_policy.py` | Prompt policy | Local-only validation and policy metadata |
| `src/ai/disabled_client.py` | Disabled client | Always raises `AIExecutionDisabledError` |
| `src/ai/readiness.py` | Readiness | Reports deferred/disabled status |

Future targets:
- `src/services` for orchestration
- `src.research` for AI-adjacent research metadata
- `src.analytics` for deterministic summaries only

