# Automation Scheduler Decommission Inventory

Canonical src.* architecture already exists. Live trading, broker/account/credential/order/deployment activation remain disabled.

Inventory summary:
- Remaining automation_scheduler files: 329
- Runtime-referenced files: 70
- Test-referenced files: 303
- Delete-ready after proof: 23

- Wrappers with runtime callers remain compatibility-only until caller migration is complete.
- Delete-ready files have no runtime/test callers and may be removed in the batched deletion phase.
- Canonical ownership is already present in `src.*` packages for the safe migrations captured here.
