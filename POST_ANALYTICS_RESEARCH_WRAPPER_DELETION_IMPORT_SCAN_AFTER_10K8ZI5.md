# Post Analytics/Research Wrapper Deletion Import Scan After 10K8ZI5

Import scans after deletion confirm the approved wrapper files are gone and the
runtime import graph now flows through canonical packages only.

Canonical import flow:
- `src.analytics`
- `src.research`
- `model_governance` package facade
- `automation_scheduler` package facade
