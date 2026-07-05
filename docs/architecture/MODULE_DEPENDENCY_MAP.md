# Module Dependency Map

This map summarizes the primary package-level dependency expectations.

| Package | Depends on | Avoids depending on |
| --- | --- | --- |
| `src.api` | `src.services`, `src.data`, `src.providers`, `src.analytics` | `src.storage` internals and high-level duplicate logic |
| `src.services` | `src.data`, `src.providers`, `src.analytics`, `src.core` | Direct runtime duplication |
| `src.backtesting` | `src.data`, `src.core`, `src.analytics` | `src.api` |
| `src.market_intelligence` | `src.data`, `src.core`, `src.providers` | `src.api` |
| `src.analytics` | `src.data`, `src.core` | `src.api` |
| `src.data` | `src.core`, `src.storage` | `src.api`, `src.services` |
| `src.providers` | `src.core`, `src.connectors` | `src.api` |
| `src.connectors` | `src.data`, `src.core` | Duplicate provider or API logic |
| `src.research` | `src.data`, `src.core`, `src.analytics` | `src.api` |
| `src.security` | `src.core`, `src.data` | `src.api` |
| `src.brokerage` | `src.core`, `src.data` | Live order submission logic |
| `src.ai` | `src.data` when needed for metadata only | Live model activation |
| `src.storage` | Low-level persistence primitives only | High-level orchestration |

## Enforcement

- Package-level direction is validated by `scripts/check_architecture.py` and the repo tests that exercise architecture guards.
- Any new dependency should preserve the lowest-owner rule and avoid copying logic into a second module.
