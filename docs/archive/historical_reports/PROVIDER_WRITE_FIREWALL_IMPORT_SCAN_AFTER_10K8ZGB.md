# Provider Write Firewall Import Scan After 10K8ZGB

## Before Redirection
- `automation_scheduler.__init__` imported `automation_scheduler.provider_write_firewall`.
- `automation_scheduler.execution_authorization` imported `automation_scheduler.provider_write_firewall`.

## After Redirection
- `automation_scheduler.__init__` imports `src.providers.policy.write_firewall`.
- `automation_scheduler.execution_authorization` imports `src.providers.policy.write_firewall`.
- `src.brokerage.readiness` supplies the live-shaped execution authorization boundary used by the scheduler.
- `automation_scheduler/provider_write_firewall.py` imports only the canonical policy module.

## Runtime Import Result
- No tracked runtime file needs `automation_scheduler.provider_write_firewall` anymore.
- The legacy file remains only as a compatibility wrapper.

## Scan Notes
- Legacy references still exist in historical tests and phase documents.
- No live/network imports were introduced by the redirection.
