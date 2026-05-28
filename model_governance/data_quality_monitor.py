from __future__ import annotations

def evaluate_data_quality(**kwargs):
    issues = []
    checks = ["missing_provider_payload", "stale_provider_payload", "duplicate_event", "book_mismatch", "market_mismatch", "selection_mismatch", "outlier_odds", "outlier_line", "bad_timestamp", "bad_numeric_field", "inconsistent_settlement_rule", "low_confidence_screenshot_parse"]
    for c in checks:
        if kwargs.get(c):
            issues.append(c)
    return {"issues": issues, "ok": len(issues) == 0, "data_quality_result": "approved" if len(issues) == 0 else "blocked_by_governance"}
