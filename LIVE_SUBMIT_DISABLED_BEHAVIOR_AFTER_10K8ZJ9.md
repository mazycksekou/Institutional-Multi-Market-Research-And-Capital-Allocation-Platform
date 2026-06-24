# Live Submit Disabled Behavior After 10K8ZJ9

The live submit interface is scaffolded but disabled.

Rules:

- `submit_live_order_disabled()` always raises `LiveSubmitDisabledError`.
- submit_live_order_disabled() always raises LiveSubmitDisabledError.
- The request object is local-only metadata.
- No network calls are made.
- No broker SDK imports are made.
