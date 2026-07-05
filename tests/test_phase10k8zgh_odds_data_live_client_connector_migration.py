from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZGH_ODDS_DATA_LIVE_CLIENT_CONNECTOR_MIGRATION.md",
    ROOT / "ODDS_DATA_LIVE_CLIENT_MIGRATION_MAP_AFTER_10K8ZGH.md",
    ROOT / "ODDS_DATA_CONNECTOR_DISABLED_LIVE_BEHAVIOR_AFTER_10K8ZGH.md",
    ROOT / "ODDS_DATA_LEGACY_COMPATIBILITY_AFTER_10K8ZGH.md",
    ROOT / "ODDS_DATA_DELETE_READINESS_AFTER_10K8ZGH.md",
]

NEW_MODULES = [
    "src.connectors.odds_data",
    "src.connectors.odds_data.configuration",
    "src.connectors.odds_data.auth",
    "src.connectors.odds_data.transport",
    "src.connectors.odds_data.readiness",
    "src.connectors.odds_data.source_profile",
    "src.connectors.odds_data.live_client",
    "src.connectors.odds_data.disabled_client",
]

LEGACY_MODULES = [
    # These legacy shells were deleted in later phases and are kept here only
    # as historical deletion evidence for the connector migration narrative.
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
    "Odds-data live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, scraping, broker execution, bet execution, AI/LLM calls, route rewrites, or deletion of legacy modules.",
    "No deletion occurred",
    "No live calls were made",
    "No credentials were read at import time",
    "src.connectors.odds_data",
    "src.connectors.market_data",
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


def test_docs_capture_odds_data_connector_migration() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for section in REQUIRED_SECTIONS:
        assert section in combined, f"missing section: {section}"

    for required in REQUIRED_STRINGS:
        assert required in combined, f"missing string: {required}"

    for tag in REQUIRED_TAGS:
        assert tag in combined, f"missing tag: {tag}"

    for forbidden in ["AKIA", "ASIA", "your_real_secret"]:
        assert forbidden not in combined


def test_odds_data_connector_modules_import_and_disable_cleanly() -> None:
    for module_name in NEW_MODULES:
        imported = importlib.import_module(module_name)
        assert imported is not None

    connector_pkg = importlib.import_module("src.connectors.odds_data")
    configuration = importlib.import_module("src.connectors.odds_data.configuration")
    auth = importlib.import_module("src.connectors.odds_data.auth")
    transport = importlib.import_module("src.connectors.odds_data.transport")
    readiness = importlib.import_module("src.connectors.odds_data.readiness")
    source_profile = importlib.import_module("src.connectors.odds_data.source_profile")
    live_client = importlib.import_module("src.connectors.odds_data.live_client")
    disabled_client = importlib.import_module("src.connectors.odds_data.disabled_client")
    errors = importlib.import_module("src.connectors.errors")

    assert connector_pkg.OddsDataReadOnlyClient.__name__ == "OddsDataReadOnlyClient"
    assert configuration.build_odds_data_connector_configuration().credential_names == (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    )
    assert auth.build_odds_data_auth_requirement().credential_names == (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    )
    assert readiness.describe_odds_data_connector_readiness()["status"] == "disabled"
    assert all(alias.startswith("legacy_") for alias in source_profile.build_odds_data_source_profile().legacy_aliases)

    live = live_client.build_odds_data_live_client()
    disabled = disabled_client.build_odds_data_disabled_live_client()
    transport_client = transport.build_odds_data_transport()

    with pytest.raises(errors.ConnectorDisabledError):
        live.fetch_odds()
    with pytest.raises(errors.ConnectorDisabledError):
        live.fetch_events()
    with pytest.raises(errors.ConnectorDisabledError):
        live.fetch_books()
    with pytest.raises(errors.ConnectorDisabledError):
        live.fetch_snapshot()
    with pytest.raises(errors.ConnectorDisabledError):
        live.request("GET", "/odds")
    with pytest.raises(errors.ConnectorDisabledError):
        live.sign_request()
    with pytest.raises(errors.ConnectorDisabledError):
        disabled.fetch_odds()
    with pytest.raises(errors.ConnectorDisabledError):
        transport_client.fetch_odds()
    with pytest.raises(errors.ConnectorDisabledError):
        transport_client.request("GET", "/odds")


def test_odds_data_connector_paths_are_vendor_neutral_and_import_safe() -> None:
    package_root = ROOT / "src" / "connectors" / "odds_data"
    assert not list(package_root.glob("sharp*.py"))
    assert not list(package_root.glob("the_odds_api*.py"))
    assert not list(package_root.glob("sportsgameodds*.py"))

    combined = "".join(
        _read(path)
        for path in [
            ROOT / "src" / "connectors" / "odds_data" / "__init__.py",
            ROOT / "src" / "connectors" / "odds_data" / "configuration.py",
            ROOT / "src" / "connectors" / "odds_data" / "auth.py",
            ROOT / "src" / "connectors" / "odds_data" / "transport.py",
            ROOT / "src" / "connectors" / "odds_data" / "readiness.py",
            ROOT / "src" / "connectors" / "odds_data" / "source_profile.py",
            ROOT / "src" / "connectors" / "odds_data" / "live_client.py",
            ROOT / "src" / "connectors" / "odds_data" / "disabled_client.py",
        ]
    )

    for bad in FORBIDDEN + ["os.getenv", "os.environ[", "SHARP_API_KEY", "THE_ODDS_API_KEY", "SPORTSGAMEODDS_API_KEY"]:
        assert bad not in combined

    assert "ConnectorDisabledError" in combined
    assert "odds_data" in combined
    assert (ROOT / "main.py").exists()
    assert (ROOT / "streamlit_app.py").exists()


def test_deleted_legacy_odds_modules_stay_deleted() -> None:
    deleted_modules = [
        "sharp_client",
        "providers.sharp_provider",
        "betting_providers.sharp_api",
        "betting_providers.the_odds_api",
        "betting_providers.sportsgameodds",
        'src.automation_scheduler_legacy.sharp_sportsbook_adapter',
        'src.automation_scheduler_legacy.sportsbook_odds_provider',
    ]

    for module_name in deleted_modules:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)
