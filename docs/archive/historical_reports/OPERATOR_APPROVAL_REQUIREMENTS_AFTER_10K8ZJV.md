# Operator Approval Requirements After 10K8ZJV

## Requirements
- Approval metadata must be supplied explicitly.
- The request remains local-only and deterministic.
- The approval record can be assembled without persistence.

## Ownership
- `src.brokerage.operator` owns operator approval metadata.
- `src.brokerage.approval` still owns the canonical live-activation gate.

## Disabled State
- Default approval is denied.
- No live activation is authorized by this interface.

