from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rollout_plan() -> None:
    docs = (
        "CONTROLLED_ROLLOUT_PLAN_AFTER_10K8ZK4.md",
        "SANDBOX_TO_PRODUCTION_SEQUENCE_AFTER_10K8ZK4.md",
        "RISK_REDUCTION_PLAN_AFTER_10K8ZK4.md",
        "OPERATOR_SIGNOFF_CHECKLIST_AFTER_10K8ZK4.md",
    )
    for name in docs:
        assert (ROOT / name).exists(), name

    rollout_text = (ROOT / "CONTROLLED_ROLLOUT_PLAN_AFTER_10K8ZK4.md").read_text(encoding="utf-8")
    for step in ("local validation", "sandbox validation", "broker certification", "monitoring verification", "rollback verification", "production approval", "controlled rollout"):
        assert step in rollout_text

    signoff_text = (ROOT / "OPERATOR_SIGNOFF_CHECKLIST_AFTER_10K8ZK4.md").read_text(encoding="utf-8")
    assert "Without explicit signoff, live trading remains disabled." in signoff_text
