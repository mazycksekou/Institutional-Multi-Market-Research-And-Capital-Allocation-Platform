# Core Probability Ownership Map After 10K8ZH5

## Ownership
- `src/core/probability.py` owns probability normalization, clamping, blending, and confidence helpers.
- `model_probability.py` is a compatibility wrapper.

## Migration Notes
- Probability logic is now canonical in `src/core.probability`.
- canonical target: `src/core/probability.py`
- The legacy module remains importable for downstream compatibility.
