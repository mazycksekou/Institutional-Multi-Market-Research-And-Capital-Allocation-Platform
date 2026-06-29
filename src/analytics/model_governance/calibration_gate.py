from __future__ import annotations
import math


def evaluate_calibration_gate(
    *,
    brier_score: float,
    log_loss: float,
    ignorance_score: float,
    expected_calibration_error: float,
    overconfidence_penalty: float,
    sample_size: int,
    market_specific_calibration: float = 80,
    sport_specific_calibration: float = 80,
    overconfidence_detected: bool | None = None,
):
    quality = 100 - (
        brier_score * 100
        + log_loss * 10
        + ignorance_score * 5
        + expected_calibration_error * 100
        + overconfidence_penalty * 5
    )
    quality = max(0.0, min(100.0, quality))
    if sample_size < 30:
        quality *= 0.7
    if overconfidence_detected:
        quality *= 0.9
    quality = (quality + market_specific_calibration + sport_specific_calibration) / 3
    status = "backtest_complete"
    if sample_size < 30:
        status = "needs_more_sample"
    if overconfidence_detected or expected_calibration_error > 0.08:
        status = "needs_revalidation"
    return {
        "Brier score": brier_score,
        "log loss": log_loss,
        "ignorance score": ignorance_score,
        "expected calibration error": expected_calibration_error,
        "calibration bucket reliability": market_specific_calibration,
        "overconfidence penalty": overconfidence_penalty,
        "sample_size": sample_size,
        "market-specific calibration": market_specific_calibration,
        "sport-specific calibration": sport_specific_calibration,
        "calibration_score": round(quality, 2),
        "passes_gate": quality >= 70,
        "calibration_status": status,
        "blocked_reasons": ["blocked_by_calibration"] if status == "needs_revalidation" else [],
    }
