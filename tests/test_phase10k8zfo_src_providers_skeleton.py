from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_ROOT = ROOT / "src" / "providers"
REPORT_PATH = ROOT / "PHASE10K8ZFO_SRC_PROVIDERS_SKELETON.md"

EXPECTED_MODULES = [
    "src.providers",
    "src.providers.base",
    "src.providers.contracts",
    "src.providers.errors",
    "src.providers.registry",
    "src.providers.health",
    "src.providers.normalization",
    "src.providers.adapters",
    "src.providers.prediction_markets",
    "src.providers.zero_dte_stocks",
    "src.providers.sportsbooks",
]

FORBIDDEN_IMPORT_PREFIXES = (
    'src.automation_scheduler_legacy',
    "betting_providers",
    "providers",
)

FORBIDDEN_DIRECT_IMPORTS = {
    "requests",
    "httpx",
    "yfinance",
    "fastapi",
    "pandas",
    "pyarrow",
}


def _module_file(module_name: str) -> Path:
    parts = module_name.split(".")
    if module_name == "src.providers":
        return PROVIDER_ROOT / "__init__.py"
    if module_name == "src.providers.adapters":
        return PROVIDER_ROOT / "adapters" / "__init__.py"
    if module_name == "src.providers.prediction_markets":
        return PROVIDER_ROOT / "prediction_markets" / "__init__.py"
    if module_name == "src.providers.zero_dte_stocks":
        return PROVIDER_ROOT / "zero_dte_stocks" / "__init__.py"
    if module_name == "src.providers.sportsbooks":
        return PROVIDER_ROOT / "sportsbooks" / "__init__.py"
    return PROVIDER_ROOT / f"{parts[-1]}.py"


def _import_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return names


def test_src_providers_skeleton_is_import_safe_and_scaffold_only(monkeypatch):
    assert PROVIDER_ROOT.is_dir()

    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    imported = {}
    for module_name in EXPECTED_MODULES:
        imported[module_name] = importlib.import_module(module_name)

    assert hasattr(imported["src.providers"], "ProviderContract")
    assert hasattr(imported["src.providers"], "ProviderRegistry")
    assert hasattr(imported["src.providers"], "ProviderHealthStatus")
    assert hasattr(imported["src.providers"], "normalize_provider_payload")
    assert hasattr(imported["src.providers"], "ProviderError")

    for module_name in EXPECTED_MODULES:
        path = _module_file(module_name)
        names = _import_names(path)
        for name in names:
            assert not any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES)
            assert name not in FORBIDDEN_DIRECT_IMPORTS


def test_provider_registry_starts_empty_and_scaffold_only():
    from src.providers.contracts import ProviderContract, build_scaffold_provider_contract
    from src.providers.health import build_scaffold_health_status
    from src.providers.normalization import normalize_provider_payload
    from src.providers.registry import ProviderRegistry, create_provider_registry

    registry = ProviderRegistry()
    assert registry.is_empty()
    assert len(registry) == 0
    assert registry.list() == []
    assert registry.snapshot() == {}
    assert create_provider_registry().is_empty()

    contract = build_scaffold_provider_contract("alpha", "Alpha", "prediction_market")
    assert isinstance(contract, ProviderContract)
    contract_dict = contract.as_dict()
    assert contract_dict["provider_id"] == "alpha"
    assert contract_dict["contract_status"] == "scaffold_only"
    assert contract_dict["dry_run"] is True

    health = build_scaffold_health_status("alpha", provider_name="Alpha", provider_type="prediction_market")
    assert health.status == "scaffold_only"
    assert health.as_dict()["provider_id"] == "alpha"

    payload = {"provider_id": "alpha", "price": 1.23}
    normalized = normalize_provider_payload("prediction_market", payload)
    assert normalized is not payload
    assert normalized["provider_id"] == "alpha"
    assert normalized["price"] == 1.23
    assert normalized["provider_type"] == "prediction_market"


def test_report_exists_and_contains_required_boundary_strings():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "src/providers/ now exists as the future canonical provider landing zone." in text
    assert "prediction_markets" in text
    assert "zero_dte_stocks" in text
    assert "sportsbooks" in text
    assert "vendor-neutral" in text
    assert "does not migrate runtime provider logic" in text
    assert "does not delete legacy provider modules" in text
    assert "does not change production behavior" in text
    assert "Import Safety Guarantees" in text
    assert "No-Network Guarantee" in text
    assert "Credential Safety Guarantee" in text
    assert "automation_scheduler" in text
    assert "Next Recommended Phase" in text


def test_canonical_provider_paths_are_vendor_neutral():
    assert (PROVIDER_ROOT / "prediction_markets").is_dir()
    assert (PROVIDER_ROOT / "zero_dte_stocks").is_dir()
    assert (PROVIDER_ROOT / "sportsbooks").is_dir()
    assert not (PROVIDER_ROOT / "kalshi").exists()

    for path in PROVIDER_ROOT.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        lowered_parts = {part.lower() for part in path.parts}
        assert "kalshi" not in lowered_parts
        assert "sharp" not in lowered_parts


def test_no_legacy_provider_dependencies_are_built_into_skeleton():
    for module_name in EXPECTED_MODULES:
        path = _module_file(module_name)
        if path.name == "__init__.py" or "policy" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert "automation_scheduler" not in text
        assert "betting_providers" not in text
        assert "from providers" not in text
        assert "import providers" not in text
        assert "requests" not in text
        assert "httpx" not in text
        assert "yfinance" not in text
        assert "kalshi" not in text.lower()
        assert "sharp" not in text.lower()
