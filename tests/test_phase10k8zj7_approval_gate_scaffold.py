from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(name: str):
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(name)


def test_approval_gate_docs_exist_and_describe_disabled_scaffold() -> None:
    docs = [
        ROOT / "PHASE10K8ZJ7_APPROVAL_GATE_SCAFFOLD.md",
        ROOT / "LIVE_APPROVAL_REQUIREMENTS_AFTER_10K8ZJ7.md",
        ROOT / "LIVE_APPROVAL_DISABLED_BEHAVIOR_AFTER_10K8ZJ7.md",
    ]
    for path in docs:
        assert path.is_file(), path

    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "approval gate remains local-only",
        "default approval state blocks live activation.",
        "require_live_approval() raises unless all required approval requirements are satisfied.",
        "live trading remains disabled in this phase.",
    ]:
        assert phrase in text


def test_approval_gate_scaffold_imports_and_evaluates_local_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    approval = _fresh_import("src.brokerage.approval")

    assert brokerage.ApprovalState.__module__ == "src.brokerage.approval"
    assert brokerage.ApprovalRequirement.__module__ == "src.brokerage.approval"
    assert brokerage.ApprovalGateStatus.__module__ == "src.brokerage.approval"

    default_state = approval.ApprovalState(approval_id="approval-default")
    default_gate = approval.evaluate_approval_gate(default_state)
    assert default_gate.ready is False
    assert default_gate.live_activation_allowed is False
    assert default_gate.status == "approval_missing"
    assert "missing_required_approvals" in default_gate.blockers

    with pytest.raises(approval.ApprovalMissingError):
        approval.require_live_approval()

    requirements = tuple(
        approval.ApprovalRequirement(
            name=item.name,
            required=item.required,
            satisfied=True,
            description=item.description,
        )
        for item in approval.build_default_approval_requirements()
    )
    satisfied_state = approval.ApprovalState(
        approval_id="approval-satisfied",
        status="approved",
        approved=True,
        requirements=requirements,
    )
    satisfied_gate = approval.evaluate_approval_gate(satisfied_state)
    assert satisfied_gate.ready is True
    assert satisfied_gate.live_activation_allowed is False
    assert satisfied_gate.decision.approved is True
    assert approval.require_live_approval(satisfied_state).approved is True

    denied_state = approval.ApprovalState(
        approval_id="approval-denied",
        status="rejected",
        approved=False,
        denied=True,
        requirements=requirements,
    )
    with pytest.raises(approval.ApprovalRejectedError):
        approval.require_live_approval(denied_state)
