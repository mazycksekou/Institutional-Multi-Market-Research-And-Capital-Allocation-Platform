# Next Execution Helper Deletion Plan After 10K8ZIP

1. Redirect the remaining runtime wrapper imports to `src.services.*` / `src.brokerage.*`.
2. Update historical proof tests to validate canonical ownership instead of wrapper ownership.
3. Re-run delete-readiness proof.
4. Delete only files that become `DELETE_READY_AFTER_PROOF`.

