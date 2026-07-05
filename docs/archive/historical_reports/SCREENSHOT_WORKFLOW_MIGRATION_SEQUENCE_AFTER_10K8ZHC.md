# Screenshot Workflow Migration Sequence After 10K8ZHC

1. Keep `screenshot_intake.py` importable as a compatibility surface.
2. Move pure screenshot workflow orchestration into `src/services/screenshot_workflow.py`.
3. Preserve `src.core` as the home for scoring/pricing/probability math.
4. Preserve provider/connector bridge usage through canonical services only.
5. Do not add OCR expansion, live connector behavior, or AI/LLM behavior in this phase.
