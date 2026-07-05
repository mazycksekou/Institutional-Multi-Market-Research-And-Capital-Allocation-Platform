# Next Analytics / Research Plan After 10K8ZHM

## Recommended Order

1. Define `src.analytics` package boundaries and reporting contracts.
2. Move attribution/performance/gov reporting into `src.analytics`.
3. Define `src.research` package boundaries and experiment contracts.
4. Move research-lane schemas and stores into `src.research`.
5. Reclassify remaining scheduler helpers after analytics/research land.

## Guardrails

- keep core math/risk pure
- keep services orchestration-only
- keep APIs thin
- do not start AI/LLM implementation yet
- do not start brokerage/live execution yet

