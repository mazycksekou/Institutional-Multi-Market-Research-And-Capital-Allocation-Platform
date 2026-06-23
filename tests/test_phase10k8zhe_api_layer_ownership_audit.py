from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHE_API_LAYER_OWNERSHIP_AUDIT.md",
    ROOT / "API_ROUTE_OWNERSHIP_MAP_AFTER_10K8ZHE.md",
    ROOT / "API_LAYER_THINNING_SEQUENCE_AFTER_10K8ZHE.md",
]


def test_api_docs_state_route_exposure_only() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS).lower()
    for phrase in [
        "api_layer_only",
        "compatibility_shim_candidate",
        "unsafe_to_touch",
        "src/api/provider_status_routes.py",
        "automation_scheduler",
        "src.providers.provider_router.providerrouter",
        "route exposure only",
    ]:
        assert phrase in text


def test_api_route_modules_import_safely() -> None:
    modules = [
        "src.api.model_card_service",
        "src.api.market_metadata_routes",
        "src.api.market_utility_routes",
        "src.api.betting_action_routes",
        "src.api.quant_routes",
        "src.api.system_routes",
        "src.api.performance_routes",
        "src.api.debug_routes",
        "src.api.provider_status_routes",
    ]
    imported = [importlib.import_module(name) for name in modules]
    assert [module.__name__ for module in imported] == modules


def test_api_model_card_service_uses_canonical_provider_router() -> None:
    module = importlib.import_module("src.api.model_card_service")
    service = module.ModelCardService()
    assert service.provider_router.__class__.__name__ == "ProviderRouter"


def test_provider_status_route_source_still_marks_scheduler_coupling() -> None:
    text = (ROOT / "src/api/provider_status_routes.py").read_text(encoding="utf-8")
    assert "import automation_scheduler" in text
