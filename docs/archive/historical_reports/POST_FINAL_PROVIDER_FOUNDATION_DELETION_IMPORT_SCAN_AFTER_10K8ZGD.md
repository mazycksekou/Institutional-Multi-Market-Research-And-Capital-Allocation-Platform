Import Scan After Deletion
==========================

- `automation_scheduler/provider_registry.py`: deleted
- `automation_scheduler/provider_write_firewall.py`: deleted
- No tracked runtime file imports either deleted shim.
- No tracked runtime file imports their legacy module paths.
- Canonical replacements remain importable:
  - `src.providers.registry`
  - `src.providers.policy.write_firewall`

Runtime Result
--------------
- The final provider-foundation blocker wrappers are gone.
- Import redirection is complete.

Only the final proof-backed provider foundation compatibility shims are deleted in this phase. Runtime modules, dashboard files, entrypoints, live clients, connector scaffolds, AI scaffolds, and brokerage scaffolds are preserved.
