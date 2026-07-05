"""Prediction-market provider namespace for the future canonical provider package."""

from .contracts import (
    PREDICTION_MARKET_PROVIDER_TYPE,
    PredictionMarketProviderContract,
    SAMPLE_DRY_RUN_PAYLOAD,
    build_prediction_market_provider_contract,
    normalize_prediction_market_payload,
    validate_prediction_market_payload,
)
from .adapters import (
    PREDICTION_MARKET_PROVIDER_TYPE as ADAPTER_PREDICTION_MARKET_PROVIDER_TYPE,
    PredictionMarketEventQuote,
    PredictionMarketProviderAdapter,
    PredictionMarketQuote,
    build_prediction_market_event_quote,
    build_prediction_market_quote,
    build_prediction_market_snapshot,
    normalize_prediction_market_event,
    normalize_prediction_market_quote,
    normalize_prediction_market_snapshot,
)

__all__ = [
    "ADAPTER_PREDICTION_MARKET_PROVIDER_TYPE",
    "PREDICTION_MARKET_PROVIDER_TYPE",
    "PredictionMarketEventQuote",
    "PredictionMarketProviderAdapter",
    "PredictionMarketProviderContract",
    "PredictionMarketQuote",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "build_prediction_market_event_quote",
    "build_prediction_market_provider_contract",
    "build_prediction_market_quote",
    "build_prediction_market_snapshot",
    "normalize_prediction_market_event",
    "normalize_prediction_market_payload",
    "normalize_prediction_market_quote",
    "normalize_prediction_market_snapshot",
    "validate_prediction_market_payload",
]
