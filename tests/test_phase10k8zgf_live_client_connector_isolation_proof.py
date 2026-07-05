from __future__ import annotations

import importlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGF_LIVE_CLIENT_CONNECTOR_ISOLATION_PROOF.md",
    ROOT / "LIVE_CLIENT_CONNECTOR_INVENTORY_AFTER_10K8ZGF.md",
    ROOT / "LIVE_CLIENT_CREDENTIAL_AND_NETWORK_RISK_MAP_AFTER_10K8ZGF.md",
    ROOT / "LIVE_CLIENT_TO_CONNECTOR_TRANSPORT_PLAN_AFTER_10K8ZGF.md",
    ROOT / "LEGACY_LIVE_CLIENT_DELETE_READINESS_AFTER_10K8ZGF.md",
    ROOT / "NEXT_CONNECTOR_MIGRATION_SEQUENCE_AFTER_10K8ZGF.md",
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


def test_live_client_isolation_docs_and_tags() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Big-Picture Architecture",
        "Live-Client Surfaces Reviewed",
        "Connector Destinations",
        "Provider Normalization Only",
        "Service Orchestration Only",
        "Credential-Risk Findings",
        "Network-Risk Findings",
        "Delete-Readiness Findings",
        "Recommended Next 3 Phases",
    ]:
        assert section in combined, f"missing section: {section}"

    for tag in REQUIRED_TAGS:
        assert tag in combined, f"missing tag: {tag}"

    for needle in [
        "Live-client functionality must be isolated into src.connectors before legacy live-client modules are deleted. This phase does not authorize live API calls, credential reads, scraping, broker execution, AI/LLM calls, source migration, or deletion.",
        "No deletion occurred",
            "No source migration occurred",
            "No live calls were made",
            "src.connectors.prediction_market_data",
            "src.connectors.odds_data",
            "src.connectors.market_data",
            "No reviewed live-client surface currently belongs directly here in this batch.",
            "Provider Normalization Only",
            "Service Orchestration Only",
            "main.py",
            "streamlit_app.py",
            "not deletion candidates",
        ]:
            assert needle in combined

    for forbidden in ["AKIA", "ASIA", "your_real_secret"]:
        assert forbidden not in combined


def test_connector_and_provider_packages_import_safely() -> None:
    modules = [
        "src.connectors",
        "src.connectors.prediction_market_data",
        "src.connectors.odds_data",
        "src.connectors.market_data",
        "src.providers",
        "src.providers.prediction_markets",
        "src.providers.sportsbooks",
    ]
    for name in modules:
        imported = importlib.import_module(name)
        assert imported is not None

    connectors_init = _read(ROOT / "src" / "connectors" / "__init__.py")
    providers_init = _read(ROOT / "src" / "providers" / "__init__.py")

    for bad in ["requests", "httpx", "yfinance", "selenium", "playwright", "websocket", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]:
        assert bad not in connectors_init
        assert bad not in providers_init


def test_bridge_shells_are_not_deletion_candidates() -> None:
    combined = "\n".join(_read(path) for path in DOCS)
    assert "main.py" in combined
    assert "streamlit_app.py" in combined
    assert "not deletion candidates" in combined
    assert (ROOT / "main.py").exists()
    assert (ROOT / "streamlit_app.py").exists()

    for path in [
        ROOT / "main.py",
        ROOT / "streamlit_app.py",
        ROOT / "src" / "api" / "model_card_service.py",
        ROOT / "src" / "api" / "provider_status_routes.py",
        ROOT / "src" / "api" / "market_metadata_routes.py",
        ROOT / "src" / "services" / "enrichment_service.py",
        ROOT / "src" / "services" / "screenshot_intake.py",
    ]:
        assert path.exists()

    assert re.search(r"AKIA[0-9A-Z]{16}", combined) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", combined) is None
    assert "your_real_secret" not in combined
