# Options GEX / Vanna Model After 10K8ZL5

- `GEX = OI * 100 * Gamma * S^2 * 0.01`
- Calls are positive.
- Puts are negative.
- Net GEX is the signed sum of contract GEX values.
- `Vanna = -(d2 / sigma) * Gamma`
- `Vanna Exposure = OI * 100 * Vanna * S * 0.01`

This is a modeling convention because dealer inventory is not directly observable.

