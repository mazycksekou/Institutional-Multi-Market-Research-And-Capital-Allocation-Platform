from __future__ import annotations


def evaluate_calibration_gate(
    *,
    brier_score: float,
    log_loss: float,
    expected_calibration_error: float,
    calibration_bucket_reliability: float,
    overconfidence_penalty: float,
    sample_size: int,
) -> dict[str, float | bool]:
    sample_component = min(100.0, sample_size / 10.0)
    score = 100.0
    score -= min(30.0, brier_score * 100.0)
    score -= min(25.0, log_loss * 20.0)
    score -= min(20.0, expected_calibration_error * 100.0)
    score -= min(15.0, overconfidence_penalty * 100.0)
    score = (score * 0.6) + (float(calibration_bucket_reliability) * 0.25) + (sample_component * 0.15)
    calibration_score = round(max(0.0, min(100.0, score)), 2)
    return {
        "brier_score": float(brier_score),
        "log_loss": float(log_loss),
        "expected_calibration_error": float(expected_calibration_error),
        "calibration_bucket_reliability": float(calibration_bucket_reliability),
        "overconfidence_penalty": float(overconfidence_penalty),
        "sample_size": int(sample_size),
        "calibration_score": calibration_score,
        "passes_gate": calibration_score >= 70,
    }

