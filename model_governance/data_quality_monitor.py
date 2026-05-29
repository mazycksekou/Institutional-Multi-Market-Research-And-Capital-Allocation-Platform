from __future__ import annotations

def evaluate_data_quality(**kwargs):
    issues = []
    checks = [
        "missing_provider_payload",
        "stale_provider_payload",
        "duplicate_event",
        "book_mismatch",
        "market_mismatch",
        "selection_mismatch",
        "outlier_odds",
        "outlier_line",
        "bad_timestamp",
        "bad_numeric_field",
        "inconsistent_settlement_rule",
        "low_confidence_screenshot_parse",
        "provider_validation_failed",
        "provider_schema_mismatch",
    ]
    for c in checks:
        if kwargs.get(c):
            issues.append(c)
    return {
        "issues": issues,
        "ok": len(issues) == 0,
        "data_quality_result": "approved" if len(issues) == 0 else "blocked_by_governance",
        "provider_id": kwargs.get("provider_id"),
        "provider_type": kwargs.get("provider_type"),
        "payload_schema_version": kwargs.get("payload_schema_version"),
        "validation_status": kwargs.get("validation_status", "unknown"),
    }
