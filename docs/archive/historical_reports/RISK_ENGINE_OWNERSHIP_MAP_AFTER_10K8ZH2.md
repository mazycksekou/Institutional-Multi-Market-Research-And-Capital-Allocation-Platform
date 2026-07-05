# Risk Engine Ownership Map (After 10K8ZH2)

```
src/core/risk.py                     : canonical risk functions
risk_engine.py                       : compatibility shim (may import from core)
```

No broker execution, no order placement, no credential reads.
