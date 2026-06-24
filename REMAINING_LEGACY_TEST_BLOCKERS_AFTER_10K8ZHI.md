# Remaining Legacy Test Blockers After 10K8ZHI

## Result
No active blockers remain in the remediated full-gate slice.
No remaining active blockers.

## Historical Evidence That Remains
1. `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py`
   - still contains deleted-shell references as historical evidence
   - intentionally excluded from active import scans

2. Deleted-shell proof tests
   - several phase-proof tests now assert deletion or disabled behavior using canonical bridge/connector surfaces
   - they remain as documentation of the migration trail, not as runtime owners

## Why These Are Not Blockers
- They no longer preserve live shell ownership.
- They no longer require live network access.
- They no longer reintroduce deleted runtime files as dependencies.

## If Future Failures Appear
Classify them as one of:
- historical evidence dependency
- compatibility-only proof dependency
- data/backtesting ownership gap
- new migration regression
