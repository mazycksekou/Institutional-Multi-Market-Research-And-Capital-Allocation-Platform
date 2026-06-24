# Analytics Batch 1 Compatibility Report After 10K8ZHR

## Compatibility Surfaces
- Legacy `model_governance/model_validation_report.py` now re-exports canonical analytics report helpers.
- Legacy `model_governance/governance_report.py` now forwards to canonical analytics reporting.
- Legacy analytics files remain importable.

## Preserved Behavior
- The public function names remain available.
- Output stays deterministic and local-only.
- No enforcement gates were moved.

## Compatibility Blockers
- `model_governance/governance_health.py` remains preserved because it is coupled to local governance state and audit files.
- Enforcement gates remain preserved for later proof-backed migration.

## Required Statement
Legacy analytics compatibility is intentionally preserved during batch 1 so downstream imports keep working while canonical ownership moves into `src.analytics`.
