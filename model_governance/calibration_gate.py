from __future__ import annotations
import math

def evaluate_calibration_gate(*, brier_score: float, log_loss: float, ignorance_score: float, expected_calibration_error: float, overconfidence_penalty: float, sample_size: int, market_specific_calibration: float = 80, sport_specific_calibration: float = 80):
    quality = 100 - (brier_score * 100 + log_loss * 10 + ignorance_score * 5 + expected_calibration_error * 100 + overconfidence_penalty * 5)
    quality = max(0.0, min(100.0, quality))
    if sample_size < 30:
        quality *= 0.7
    quality = (quality + market_specific_calibration + sport_specific_calibration) / 3
    return {"Brier score": brier_score, "log loss": log_loss, "ignorance score": ignorance_score, "expected calibration error": expected_calibration_error, "calibration bucket reliability": market_specific_calibration, "overconfidence penalty": overconfidence_penalty, "sample_size": sample_size, "market-specific calibration": market_specific_calibration, "sport-specific calibration": sport_specific_calibration, "calibration_score": round(quality, 2), "passes_gate": quality >= 70}
