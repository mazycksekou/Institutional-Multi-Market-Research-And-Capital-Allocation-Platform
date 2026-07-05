
# Validation Framework

## Validation Order

1. Required field presence
2. Type validation
3. Missing value checks
4. Duplicate key checks
5. Join key checks
6. Time ordering checks
7. Schema version checks
8. Market compatibility checks
9. Sport compatibility checks
10. Asset compatibility checks

## Rules

| Rule | Purpose | Failure action |
| --- | --- | --- |
| Required fields | Prevent incomplete records from publishing. | Reject batch. |
| Types | Preserve schema contracts. | Reject batch. |
| Missing values | Protect downstream consumers. | Reject or quarantine batch. |
| Duplicate keys | Prevent double counting. | Reject or dedupe with audit. |
| Join keys | Preserve feature/model joins. | Reject batch. |
| Time ordering | Preserve point-in-time correctness. | Reject batch. |
| Schema version | Ensure compatibility. | Route through migration path. |
| Market compatibility | Prevent cross-market contamination. | Reject batch. |
| Sport compatibility | Preserve sport-specific constraints. | Reject batch. |
| Asset compatibility | Prevent invalid asset joins. | Reject batch. |

## Enforcement Notes

- No provider may bypass validation.
- Validation results must be persisted alongside the imported dataset.
- Validation failures should be visible to both ops workflows and dashboard surfaces.
