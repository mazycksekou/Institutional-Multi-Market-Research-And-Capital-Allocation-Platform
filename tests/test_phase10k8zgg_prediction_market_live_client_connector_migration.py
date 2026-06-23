from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGG_PREDICTION_MARKET_LIVE_CLIENT_CONNECTOR_MIGRATION.md",
    ROOT / "PREDICTION_MARKET_LIVE_CLIENT_MIGRATION_MAP_AFTER_10K8ZGG.md",
    ROOT / "PREDICTION_MARKET_CONNECTOR_DISABLED_LIVE_BEHAVIOR_AFTER_10K8ZGG.md",
    ROOT / "PREDICTION_MARKET_LEGACY_COMPATIBILITY_AFTER_10K8ZGG.md",
    ROOT / "PREDICTION_MARKET_DELETE_READINESS_AFTER_10K8ZGG.md",
]

NEW_MODULES = [
    "src.connectors.prediction_market_data",
    "src.connectors.prediction_market_data.configuration",
    "src.connectors.prediction_market_data.auth",
    "src.connectors.prediction_market_data.signing",
    "src.connectors.prediction_market_data.transport",
    "src.connectors.prediction_market_data.readiness",
    "src.connectors.prediction_market_data.disabled_client",
]

FORBIDDEN = [
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "websocket",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
]

REQUIRED_SECTIONS = [
    "Executive Summary",
    "Current HEAD",
    "Purpose",
    "Scope",
    "Non-Goals",
    "Big-Picture Architecture",
    "Live-Client Shape Transported",
    "Connector-Owned Modules Created",
    "Credentials as Data Only",
    "Disabled Live Methods",
    "Legacy Modules Reviewed",
    "Compatibility Policy",
    "Delete-Readiness",
    "Remaining Work",
    "Next Recommended Phase",
]

REQUIRED_STRINGS = [
    "Prediction-market live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, request signing, scraping, broker execution, AI/LLM calls, route rewrites, or deletion of legacy modules.",
    "No deletion occurred",
    "No live calls were made",
    "No credentials were read at import time",
    "src.connectors.prediction_market_data",
    "src.connectors.market_data",
    "reserved for future stock / 0DTE live access",
    "main.py",
    "streamlit_app.py",
]

REQUIRED_TAGS = [
    "CONNECTOR_READY_INERT",
    "CONNECTOR_READY_WITH_STUBS",
    "PROVIDER_NORMALIZATION_ONLY",
    "SERVICE_ORCHESTRATION_ONLY",
    "RUNTIME_LIVE_CLIENT_OWNER",
    "CREDENTIAL_RISK",
    "NETWORK_RISK",
    "DELETE_READY_AFTER_CONNECTOR_MIGRATION",
    "UNSAFE_TO_TOUCH",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_docs_capture_prediction_market_connector_migration() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in REQUIRED_SECTIONS:
        assert section in combined, f"missing section: {section}"

    for required in REQUIRED_STRINGS:
        assert required in combined, f"missing string: {required}"

    for tag in REQUIRED_TAGS:
        assert tag in combined, f"missing tag: {tag}"

    for forbidden in ["AKIA", "ASIA", "your_real_secret"]:
        assert forbidden not in combined


def test_prediction_market_connector_modules_import_and_disable_cleanly() -> None:
    for module_name in NEW_MODULES:
        imported = importlib.import_module(module_name)
        assert imported is not None

    connector_pkg = importlib.import_module("src.connectors.prediction_market_data")
    configuration = importlib.import_module("src.connectors.prediction_market_data.configuration")
    auth = importlib.import_module("src.connectors.prediction_market_data.auth")
    signing = importlib.import_module("src.connectors.prediction_market_data.signing")
    transport = importlib.import_module("src.connectors.prediction_market_data.transport")
    readiness = importlib.import_module("src.connectors.prediction_market_data.readiness")
    disabled_client = importlib.import_module("src.connectors.prediction_market_data.disabled_client")

    assert connector_pkg.PredictionMarketReadOnlyClient.__name__ == "PredictionMarketReadOnlyClient"
    assert configuration.build_prediction_market_connector_configuration().credential_names == (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    )
    assert auth.build_prediction_market_auth_requirement().credential_names == (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    )
    assert readiness.describe_prediction_market_connector_readiness()["status"] == "disabled"

    with pytest.raises(importlib.import_module("src.connectors.errors").ConnectorDisabledError):
        signing.sign_prediction_market_request()

    transport_client = transport.build_prediction_market_transport()
    disabled_live_client = disabled_client.build_prediction_market_disabled_live_client()

    with pytest.raises(importlib.import_module("src.connectors.errors").ConnectorDisabledError):
        transport_client.request("GET", "/markets")
    with pytest.raises(importlib.import_module("src.connectors.errors").ConnectorDisabledError):
        transport_client.fetch_markets()
    with pytest.raises(importlib.import_module("src.connectors.errors").ConnectorDisabledError):
        disabled_live_client.fetch_markets()
    with pytest.raises(importlib.import_module("src.connectors.errors").ConnectorDisabledError):
        disabled_live_client.sign_request()

    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        assert "kalshi_client" in text or "legacy" in text.lower()


def test_connector_package_is_vendor_neutral_and_import_safe() -> None:
    package_root = ROOT / "src" / "connectors" / "prediction_market_data"
    assert not list(package_root.glob("kalshi*.py"))
    assert not list(package_root.glob("*.pyi"))

    combined = "".join(_read(path) for path in [
        ROOT / "src" / "connectors" / "prediction_market_data" / "__init__.py",
        ROOT / "src" / "connectors" / "prediction_market_data" / "configuration.py",
        ROOT / "src" / "connectors" / "prediction_market_data" / "auth.py",
        ROOT / "src" / "connectors" / "prediction_market_data" / "signing.py",
        ROOT / "src" / "connectors" / "prediction_market_data" / "transport.py",
        ROOT / "src" / "connectors" / "prediction_market_data" / "readiness.py",
        ROOT / "src" / "connectors" / "prediction_market_data" / "disabled_client.py",
    ])

    for bad in FORBIDDEN + ["os.getenv", "os.environ[", "KALSHI_API_KEY", "KALSHI_PRIVATE_KEY"]:
        assert bad not in combined

    assert "ConnectorDisabledError" in combined
    assert "prediction_market_data" in combined
    assert (ROOT / "main.py").exists()
    assert (ROOT / "streamlit_app.py").exists()
