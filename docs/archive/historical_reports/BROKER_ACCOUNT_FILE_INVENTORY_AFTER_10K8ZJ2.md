# Broker Account File Inventory After 10K8ZJ2

| File | Classification | Responsibility | Canonical Target | Risk |
| --- | --- | --- | --- | --- |
| `src/brokerage/accounts.py` | `BROKER_ACCOUNT_METADATA_ONLY` | Account descriptors and disabled readiness only | `src.brokerage` | No live behavior |
| `src/brokerage/credentials.py` | `BROKER_ACCOUNT_METADATA_ONLY` | Credential descriptors and disabled validation only | `src.brokerage` | No import-time secret reads |
| `src/brokerage/reconciliation.py` | `POSITION_RECONCILIATION_RISK` | Disabled reconciliation request/result contracts | `src.brokerage` | Reconciliation remains disabled |
| `src/brokerage/readiness.py` | `BROKER_ACCOUNT_METADATA_ONLY` | Disabled execution readiness flags | `src.brokerage` | No live execution |
| `src/services/execution_service.py` | `MIGRATE_TO_SRC_SERVICES` | Small-account review and broker-quality orchestration | `src.services` | Orchestration only |
| `automation_scheduler/__init__.py` | `MIGRATE_TO_SRC_SERVICES` | Thin wrapper to service orchestration | `src.services` | Wrapper only |
| `src/api/automation_small_account_routes.py` | `MIGRATE_TO_SRC_SERVICES` | API wrapper for small-account review and risk endpoints | `src.api` -> `src.services` | API-only |
| `src/api/schemas/betting_actions.py` | `BROKER_ACCOUNT_METADATA_ONLY` | Request/response schema metadata only | `src.api.schemas` | No live execution |
| `automation_scheduler/data_source_research_lanes.py` | `BROKER_ACCOUNT_METADATA_ONLY` | Declarative account/API-key requirement metadata | `src.data` / `src.research` | Metadata only |
| `automation_scheduler/nfl_open_data_source_exhaustion.py` | `BROKER_CREDENTIAL_RISK` | Notes external API-key requirements in comments/config | `src.data` | No import-time secret reads |
| `automation_scheduler/paper_trade_ledger.py` | `LEDGER_PERSISTENCE_RISK` | Local file-backed compatibility ledger | `src.brokerage.ledger` / `src.services.ledger_service` | Local only |
| `automation_scheduler/paper_decision_ledger.py` | `LEDGER_PERSISTENCE_RISK` | Local file-backed compatibility decision ledger | `src.brokerage.ledger` / `src.services.ledger_service` | Local only |
| `src/services/ledger_service.py` | `LEDGER_PERSISTENCE_RISK` | Canonical file-backed audit/performance ledger | `src.services` | Local persistence only |
| `bet_log.py` | `LEDGER_PERSISTENCE_RISK` | Root-level file-backed bet log | `src.services` / `src.brokerage.ledger` | Local persistence only |

No live broker SDK imports or live order submission paths were activated.

