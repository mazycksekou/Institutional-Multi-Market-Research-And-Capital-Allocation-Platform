from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHG_AUTOMATION_SCHEDULER_DECOMMISSION_AUDIT.md",
    ROOT / "AUTOMATION_SCHEDULER_REMAINING_OWNER_MAP_AFTER_10K8ZHG.md",
    ROOT / "AUTOMATION_SCHEDULER_DECOMMISSION_SEQUENCE_AFTER_10K8ZHG.md",
]


def test_scheduler_docs_state_decommission_target_and_owner_map() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS).lower()
    for phrase in [
        "automation_scheduler remains a decommission target",
        "service_orchestration_owner",
        "migrate_to_src_services",
        "dashboard_layer_only",
        "compatibility_shim_candidate",
        "unsafe_to_touch",
        "scheduler_runner.py",
        "streamlit_dashboard_data.py",
        "provider_allowlist.py",
        "data_source_registry.py",
    ]:
        assert phrase in text


def test_scheduler_canonical_bridge_modules_import_safely() -> None:
    modules = [
        "src.services.prediction_market_runtime_bridge",
        "src.services.odds_runtime_bridge",
        "src.providers.registry",
        "src.providers.health",
        "src.services.streamlit_dashboard_facade",
        'src.services.scheduler_runner',
        'src.analytics.calibration_collector',
        "src.services.settlement_service",
        'src.market_intelligence.prediction_market_outcome_candidates',
        'src.services.streamlit_dashboard_data',
    ]
    imported = [importlib.import_module(name) for name in modules]
    assert [module.__name__ for module in imported] == modules


def test_scheduler_package_still_points_to_canonical_bridges() -> None:
    text = (ROOT / 'src/services/streamlit_dashboard_facade.py').read_text(encoding="utf-8")
    assert "from src.services.odds_runtime_bridge import" in text
    assert "from src.services.prediction_market_runtime_bridge import" in text


def test_scheduler_source_scan_shows_canonical_bridge_dependencies() -> None:
    for relpath in [
        'src/services/scheduler_runner.py',
        'src/analytics/calibration_collector.py',
        "src/services/settlement_service.py",
        'src/market_intelligence/prediction_market_outcome_candidates.py',
    ]:
        text = (ROOT / relpath).read_text(encoding="utf-8")
        assert "src.services.prediction_market_runtime_bridge" in text or "src.services.odds_runtime_bridge" in text or "src.services.settlement_service" in text
