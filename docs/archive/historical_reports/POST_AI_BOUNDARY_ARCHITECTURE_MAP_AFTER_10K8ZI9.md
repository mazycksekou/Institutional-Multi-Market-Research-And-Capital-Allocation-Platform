# Post AI Boundary Architecture Map After 10K8ZI9

```mermaid
flowchart LR
    S[src.services] --> A[src.ai]
    R[src.research] --> A
    N[src.analytics] --> A
    SCH[automation_scheduler] -. deferred .-> A
```

Notes:
- `src.ai` is disabled and local-only.
- `automation_scheduler` still carries AI-adjacent legacy surfaces.
- No AI execution boundary is active.

