from __future__ import annotations

from typing import Any

from . import build_output, evaluate_registry_entry, make_model

OUTPUT_FIELDS = [
    "model_status",
    "model_risk_rating",
    "validation_required",
    "last_reviewed",
    "drift_detected",
    "approval_status",
    "audit_notes",
]

MODELS = {
    name: make_model(
        name=name,
        classification="validation_model",
        mathematical_purpose="Track governance, validation, drift, and approval state for institutional model usage.",
        required_inputs=["validation_complete", "last_reviewed_days", "drift_score", "approval_committee", "audit_notes"],
        output_fields=OUTPUT_FIELDS,
        assumptions=[
            "Validation and review metadata are recorded accurately.",
            "Governance status should gate promotion decisions.",
        ],
        limitations=[
            "Governance metadata does not replace independent validation work.",
            "These models inform controls and should not create market recommendations.",
        ],
        evidence_standard="Model risk management and institutional governance practice.",
        applicable_markets=["all"],
        review_queue_scoring_reason="Relevant only as a gating function because poor governance should block review-queue influence.",
    )
    for name in [
        "model_inventory",
        "model_risk_rating",
        "independent_validation_status",
        "assumptions_limitations_registry",
        "performance_monitoring_status",
        "data_quality_monitoring_status",
        "model_drift_detector",
        "challenger_model_result",
        "approval_status",
        "audit_trail_status",
    ]
}


def get_models() -> dict[str, dict[str, Any]]:
    return MODELS.copy()


def evaluate_governance_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    validation_complete = bool(inputs["validation_complete"])
    last_reviewed_days = max(int(inputs["last_reviewed_days"]), 0)
    drift_score = max(0.0, min(1.0, float(inputs["drift_score"])))
    approval_committee = str(inputs["approval_committee"])
    audit_notes = list(inputs["audit_notes"])
    model_status = "validated" if validation_complete and drift_score < 0.4 else "review_required"
    model_risk_rating = "high" if drift_score >= 0.6 or not validation_complete else "moderate"
    validation_required = not validation_complete
    drift_detected = drift_score >= 0.5
    approval_status = "approved" if validation_complete and approval_committee else "pending_review"
    return build_output(
        OUTPUT_FIELDS,
        {
            "model_status": model_status,
            "model_risk_rating": model_risk_rating,
            "validation_required": validation_required,
            "last_reviewed": f"{last_reviewed_days}_days_ago",
            "drift_detected": drift_detected,
            "approval_status": approval_status,
            "audit_notes": audit_notes,
            "model_name": model_name,
        },
    )


def run_model(model_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate_registry_entry(MODELS, evaluate_governance_model, model_name, inputs)
