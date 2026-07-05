# Live Approval Requirements After 10K8ZJ7

Required approval checks:

- owner approval
- broker approval
- risk approval
- security review
- rollback plan ready
- kill switch clear

Evaluation rules:

- Approval evaluation is deterministic and local-only.
- Requirements are metadata, not secret reads.
- Approval state can be satisfied for local evaluation only.
- Live behavior remains disabled in this phase.
