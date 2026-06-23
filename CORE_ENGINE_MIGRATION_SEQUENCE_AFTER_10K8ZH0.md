# Core Engine Migration Sequence (After 10K8ZH0)

1. **Batch 1 (10K8ZH1)** – Add pure math helpers to `src/core/math_utils.py`.
2. **Batch 2 (10K8ZH2)** – Add risk helpers to `src/core/risk.py`.
3. **Batch 3 (future)** – Move pricing helpers to `src/core/pricing.py`.
4. **Batch 4 (future)** – Move probability helpers to `src/core/probability.py`.
5. **Batch 5 (future)** – Move execution helpers to `src/core/execution.py`.
6. **Batch 6 (future)** – Move decision orchestration to `src/services/decision_engine.py`.
7. **Batch 7 (future)** – Delete legacy wrappers after proving no import dependencies remain.

Each batch is preceded by a planning/documentation phase.
