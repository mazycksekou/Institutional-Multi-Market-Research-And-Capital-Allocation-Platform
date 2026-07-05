# Compatibility Shell Inventory After 10K8ZMN

The shell contained `automation_scheduler/__init__.py` plus 23 wrapper modules.
Every wrapper was a one-line compatibility shim into `src.automation_scheduler_legacy`.

- Runtime wrappers: 23
- Package shim: 1
- Duplicated logic: 0
- Direct import callers: 0
- Remaining references: historical proof docs and phase tests only
