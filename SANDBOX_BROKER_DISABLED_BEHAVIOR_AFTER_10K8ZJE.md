# Sandbox Broker Disabled Behavior After 10K8ZJE

- `build_sandbox_descriptor()` constructs local metadata only.
- `build_sandbox_capabilities()` constructs disabled capability metadata only.
- `build_sandbox_status()` reports the sandbox boundary as disabled.
- No order submission, account creation, or network behavior is introduced.
