# Connector Ownership Map

## Canonical Connector Responsibilities

| Connector responsibility | Canonical owner | Notes |
| --- | --- | --- |
| External-source normalization | `src.connectors` | Main home for source adapters |
| Read-only provider adapters | `src.connectors` | Do not introduce live side effects |
| Source-specific transport glue | `src.connectors` | Keep vendor-specific details behind the adapter boundary |
| Connector metadata | `src.data` / `src.providers` | Store only what downstream consumers need |

## Guidance

- Connectors translate external shapes into canonical internal contracts.
- If a connector becomes a shared domain rule, move that rule into `src.data`, `src.core`, or `src.providers` as appropriate.
- Keep compatibility shims minimal and temporary.
