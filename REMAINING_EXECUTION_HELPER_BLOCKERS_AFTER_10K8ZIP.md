# Remaining Execution Helper Blockers After 10K8ZIP

## Runtime blockers

- Wrapper-path imports still exist in scheduler and API code.

## Test blockers

- Historical proof tests still import wrapper paths directly.

## Unsafe to touch

- No execution helper is safe to delete in this phase.

## Summary

Canonical helper modules exist, but wrapper deletion is still blocked by live runtime/test references.
