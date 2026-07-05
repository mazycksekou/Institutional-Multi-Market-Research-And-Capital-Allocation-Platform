# PHASE10K8ZJG Sandbox Submit Flow

## Scope
- `src.brokerage.sandbox_submit` models the production-shaped submit flow without enabling it.
- It uses the canonical order and execution contracts and remains disabled.

## Guarantees
- Approval state is required.
- A sandbox broker descriptor is required.
- No order submission occurs.
- No broker SDK or network behavior is introduced.
