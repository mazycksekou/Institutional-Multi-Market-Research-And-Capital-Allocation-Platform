# Analytics/Research Reference Remediation Plan After 10K8ZHZ

1. Reclassify any active tests that still depend on compatibility wrappers.
2. Keep doc-only and historical proof references separate from runtime dependency scans.
3. Revisit `automation_scheduler/model_maturity_registry.py` only after scheduler-coupled blockers are isolated.
4. Run a dedicated delete-proof phase before removing any wrapper.
