# PHASE10K8ZJF Credential Activation Boundary

## Scope
- `src.brokerage.credential_loader` models the credential-loading boundary as a disabled scaffold.
- The boundary must require ApprovalState.
- The boundary must require a clear kill switch.
- The boundary still raises a disabled error.

## Guarantees
- No environment variables are read at import time.
- No credentials are loaded in this phase.
- No network or broker SDK behavior is activated.
