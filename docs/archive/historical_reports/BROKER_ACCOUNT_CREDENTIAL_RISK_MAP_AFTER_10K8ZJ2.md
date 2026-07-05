# Broker Account Credential Risk Map After 10K8ZJ2

| File | Classification | Why |
| --- | --- | --- |
| `src/brokerage/credentials.py` | `BROKER_ACCOUNT_METADATA_ONLY` | Describes future broker credentials without reading them |
| `src/brokerage/readiness.py` | `BROKER_ACCOUNT_METADATA_ONLY` | Disabled readiness flags only; no secret access |
| `automation_scheduler/data_source_research_lanes.py` | `BROKER_ACCOUNT_METADATA_ONLY` | Declarative lane metadata only |
| `automation_scheduler/nfl_open_data_source_exhaustion.py` | `BROKER_CREDENTIAL_RISK` | Mentions API-key requirements for external data, but does not read secrets at import time |

No runtime credential reads were found.
No broker SDK or network client is imported by the new account boundary.

