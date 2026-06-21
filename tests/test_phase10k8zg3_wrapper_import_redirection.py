from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DELETED_WRAPPER_FILES = [
    "automation_scheduler/provider_contracts.py",
    "automation_scheduler/provider_health.py",
    "automation_scheduler/provider_adapter_base.py",
    "automation_scheduler/provider_normalization_contract.py",
    "automation_scheduler/provider_payload_validator.py",
    "automation_scheduler/provider_secret_policy.py",
    "providers/base_provider.py",
    "betting_providers/base.py",
    "betting_providers/normalization.py",
]

REMAINING_WRAPPER_FILES = [
]

UPDATED_FILES = {
    "main.py": [
        "from src.providers.compat import PREDICTION_MARKET",
        "from betting_providers.base import PREDICTION_MARKET",
    ],
    "screenshot_intake.py": [
        "from src.services.enrichment_service import EnrichmentService",
    ],
    "tests/test_provider_contracts.py": [
        "from src.providers.contracts import PROVIDER_TYPES, get_default_provider_contracts",
        "from automation_scheduler.provider_contracts import PROVIDER_TYPES, get_default_provider_contracts",
    ],
    "tests/test_provider_registry.py": [
        "from src.providers.registry import get_provider_registry",
    ],
    "tests/test_provider_health.py": [
        "from src.providers.contracts import get_default_provider_contracts",
        "from src.providers.health import compact_provider_health, summarize_provider_health",
        "from automation_scheduler.provider_contracts import get_default_provider_contracts",
        "from automation_scheduler.provider_health import compact_provider_health, summarize_provider_health",
    ],
    "tests/test_provider_payload_validator.py": [
        "from src.providers.validation import validate_provider_payload",
        "from automation_scheduler.provider_payload_validator import validate_provider_payload",
    ],
    "tests/test_provider_normalization_contract.py": [
        "from src.providers.normalization import get_normalized_schema, normalize_provider_payload",
        "from src.providers.sportsbooks import SAMPLE_DRY_RUN_PAYLOAD as SPORTSBOOK_SAMPLE",
        "from automation_scheduler.provider_normalization_contract import get_normalized_schema, normalize_provider_payload",
    ],
    "tests/test_provider_secret_policy.py": [
        "from src.providers.policy.secret_policy import",
        "from automation_scheduler.provider_secret_policy import",
    ],
    "tests/test_provider_adapter_base.py": [
        "from src.providers.base import ProviderAdapterBase",
        "from src.providers.contracts import get_default_provider_contracts",
        "from automation_scheduler.provider_adapter_base import ProviderAdapterBase",
    ],
    "tests/test_sportsbook_odds_provider.py": [
        "from src.providers.registry import get_provider_registry",
    ],
    "tests/test_kalshi_market_provider.py": [
        "from src.providers.registry import get_provider_registry",
    ],
    "tests/test_security_framework.py": [
        "from src.providers.policy.write_firewall import check_provider_write_attempt",
    ],
}

CANONICAL_IMPORTS = [
    "src.providers.contracts",
    "src.providers.registry",
    "src.providers.health",
    "src.providers.base",
    "src.providers.normalization",
    "src.providers.validation",
    "src.providers.policy.secret_policy",
    "src.providers.policy.write_firewall",
    "src.providers.compat",
    "src.services.enrichment_service",
]

WRAPPER_IMPORTS = [
    "automation_scheduler.provider_contracts",
    "automation_scheduler.provider_health",
    "automation_scheduler.provider_adapter_base",
    "automation_scheduler.provider_normalization_contract",
    "automation_scheduler.provider_payload_validator",
    "automation_scheduler.provider_secret_policy",
    "providers.base_provider",
    "betting_providers.base",
    "betting_providers.normalization",
]


def test_phase10k8zg3_wrapper_import_redirection():
    # Docs exist and declare the redirection strategy.
    for doc in (
        "PHASE10K8ZG3_WRAPPER_IMPORT_REDIRECTION.md",
        "WRAPPER_IMPORT_REDIRECTION_MAP_AFTER_10K8ZG3.md",
        "WRAPPER_DELETION_PROOF_AFTER_10K8ZG3.md",
        "REMAINING_LEGACY_IMPORTS_AFTER_10K8ZG3.md",
    ):
        assert (ROOT / doc).exists(), doc
        text = (ROOT / doc).read_text(encoding="utf-8")
        assert "Wrapper-only modules are not deleted in this phase. This phase redirects downstream imports and produces deletion proof only." in text

    # The thin wrappers have been deleted; the remaining bridge hooks stay on disk.
    for relpath in DELETED_WRAPPER_FILES:
        assert not (ROOT / relpath).exists(), relpath
    for relpath in REMAINING_WRAPPER_FILES:
        assert (ROOT / relpath).exists(), relpath

    # Updated files now point to canonical paths.
    for relpath, expected_snippets in UPDATED_FILES.items():
        text = (ROOT / relpath).read_text(encoding="utf-8")
        for snippet in expected_snippets:
            if snippet.startswith("from automation_scheduler") or snippet.startswith("from providers.") or snippet.startswith("from betting_providers."):
                assert snippet not in text, f"legacy import still present in {relpath}: {snippet}"
            else:
                assert snippet in text, f"canonical import missing in {relpath}: {snippet}"

    # Canonical modules import safely without import-time credential access.
    original_getenv = os.getenv
    try:
        def forbidden_getenv(*_args, **_kwargs):
            raise AssertionError("import-time credential access is forbidden")

        os.getenv = forbidden_getenv  # type: ignore[assignment]
        for module_name in CANONICAL_IMPORTS:
            sys.modules.pop(module_name, None)
            importlib.import_module(module_name)
    finally:
        os.getenv = original_getenv  # type: ignore[assignment]

    # Canonical provider/connectors trees must stay free of live-network imports.
    forbidden = {"requests", "httpx", "yfinance", "selenium", "playwright", "websocket", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"}
    for package in (ROOT / "src/providers", ROOT / "src/connectors"):
        for py_file in package.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            roots: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        roots.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    roots.add(node.module.split(".")[0])
            assert not (roots & forbidden), f"forbidden import in {py_file}: {roots & forbidden}"
            assert "automation_scheduler" not in roots
            assert "providers" not in roots
            assert "betting_providers" not in roots

    # Remaining legacy imports are documented, not removed.
    remaining_legacy = (ROOT / "REMAINING_LEGACY_IMPORTS_AFTER_10K8ZG3.md").read_text(encoding="utf-8")
    assert "main.py" in remaining_legacy
    assert "src/api/model_card_service.py" in remaining_legacy
