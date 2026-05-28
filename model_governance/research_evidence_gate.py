from __future__ import annotations

from . import contains_banned_language


def evaluate_research_evidence_gate(**kwargs):
    score = float(kwargs.get("evidence_score", 0))
    ok = all([
        score >= 70,
        kwargs.get("mathematical_definition_exists", False),
        kwargs.get("input_availability", False),
        kwargs.get("out_of_sample_testability", False),
        kwargs.get("risk_control_support", False),
        kwargs.get("no_guarantee_language", True),
    ])
    return {**kwargs, "research_evidence_gate_result": "approved" if ok else "blocked_by_governance"}
