"""Prediction-market provider namespace for the future canonical provider package."""

from .contracts import (
    PREDICTION_MARKET_PROVIDER_TYPE,
    PredictionMarketProviderContract,
    SAMPLE_DRY_RUN_PAYLOAD,
    build_prediction_market_provider_contract,
    normalize_prediction_market_payload,
    validate_prediction_market_payload,
)

__all__ = [
    "PREDICTION_MARKET_PROVIDER_TYPE",
    "PredictionMarketProviderContract",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "build_prediction_market_provider_contract",
    "normalize_prediction_market_payload",
    "validate_prediction_market_payload",
]
