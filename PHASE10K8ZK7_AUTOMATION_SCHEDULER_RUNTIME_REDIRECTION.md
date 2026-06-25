# Automation Scheduler Decommission Inventory

Canonical src.* architecture already exists. Live trading, broker/account/credential/order/deployment activation remain disabled.

Inventory summary:
- Remaining automation_scheduler files: 329
- Runtime-referenced files: 70
- Test-referenced files: 303
- Delete-ready after proof: 23

Runtime callers are explicitly justified in the import scan. Remaining active references are wrapper-based and must be removed in later phases.

Current runtime caller surfaces remain concentrated in `main.py`, `streamlit_app.py`, `src/api/*`, `src/services/*`, and compatibility wrappers under `automation_scheduler/__init__.py`.

No delete-ready file appears in the runtime reference set.
