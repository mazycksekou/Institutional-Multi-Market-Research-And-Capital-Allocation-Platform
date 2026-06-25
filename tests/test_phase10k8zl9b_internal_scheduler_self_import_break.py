from __future__ import annotations

import ast
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNED_FILES = [
    "automation_scheduler/calibration_strategy_filter.py",
    "automation_scheduler/experiment_history_store.py",
    "automation_scheduler/experiment_report_exporter.py",
    "automation_scheduler/feature_ablation_lab.py",
    "automation_scheduler/historical_backtest_bridge.py",
    "automation_scheduler/historical_line_movement.py",
    "automation_scheduler/historical_odds_sqlite.py",
    "automation_scheduler/line_movement_data_quality_dashboard.py",
    "automation_scheduler/model_data_field_catalog.py",
    "automation_scheduler/source_event_link_resolver.py",
    "automation_scheduler/streamlit_dashboard_data.py",
    "automation_scheduler/synthetic_line_movement_sandbox.py",
    "automation_scheduler/zero_dte_fixture_template.py",
]

DOCS = [
    "PHASE10K8ZL9B_INTERNAL_SCHEDULER_SELF_IMPORT_BREAK.md",
    "INTERNAL_SCHEDULER_SELF_IMPORTS_BEFORE_10K8ZL9B.md",
    "INTERNAL_SCHEDULER_CANONICAL_REDIRECTION_MAP_AFTER_10K8ZL9B.md",
    "INTERNAL_SCHEDULER_ZERO_SELF_IMPORT_PROOF_AFTER_10K8ZL9B.md",
    "NEXT_AUTOMATION_SCHEDULER_TEST_IMPORT_REDIRECTION_PLAN_AFTER_10K8ZL9B.md",
]

CANONICAL_MODULES = [
    "src.market_intelligence.feature_packs",
    "src.research.feature_control",
    "src.research.history",
    "src.data.field_catalog",
    "src.data.historical_sources",
    "src.data.historical_odds",
    "src.data.line_movement",
    "src.data.source_event_links",
    "src.backtesting.dataset_builder",
    "src.backtesting.strategy_profiles",
    "src.backtesting.engine",
    "src.backtesting.historical_bridge",
]

EXPECTED_REDIRECTS = {
    "automation_scheduler/calibration_strategy_filter.py": "src.market_intelligence.feature_packs",
    "automation_scheduler/experiment_history_store.py": "src.research.feature_control",
    "automation_scheduler/experiment_report_exporter.py": "src.research.history",
    "automation_scheduler/feature_ablation_lab.py": "src.market_intelligence.feature_packs",
    "automation_scheduler/historical_backtest_bridge.py": "src.backtesting.engine",
    "automation_scheduler/historical_line_movement.py": "src.data.historical_odds",
    "automation_scheduler/historical_odds_sqlite.py": "src.data.historical_odds",
    "automation_scheduler/line_movement_data_quality_dashboard.py": "src.data.line_movement",
    "automation_scheduler/model_data_field_catalog.py": "src.data.field_catalog",
    "automation_scheduler/source_event_link_resolver.py": "src.data.historical_odds",
    "automation_scheduler/streamlit_dashboard_data.py": "src.data.historical_sources",
    "automation_scheduler/synthetic_line_movement_sandbox.py": "src.data.line_movement",
    "automation_scheduler/zero_dte_fixture_template.py": "src.data.field_catalog",
}

FORBIDDEN_MARKERS = [
    "requests",
    "httpx",
    "websocket",
    "openai",
    "deepseek",
    "api_key",
    "load_credentials",
    "create_account",
    "submit_order",
    "place_order",
    "broker_sdk",
]


def _direct_import_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_phase10k8zl9b_internal_scheduler_self_import_break() -> None:
    for doc in DOCS:
        assert (ROOT / doc).exists(), doc

    for rel_path in SCANNED_FILES:
        path = ROOT / rel_path
        assert path.exists(), rel_path
        text = path.read_text(encoding="utf-8")
        assert EXPECTED_REDIRECTS[rel_path] in text
        modules = _direct_import_modules(path)
        assert all(not module.startswith("automation_scheduler") for module in modules), modules
        lowered = text.lower()
        for marker in FORBIDDEN_MARKERS:
            assert marker not in lowered, (rel_path, marker)

    assert (ROOT / "automation_scheduler").exists()

    for module_name in CANONICAL_MODULES:
        importlib.import_module(module_name)

    from src.market_intelligence.feature_packs import evaluate_sport_feature_readiness, normalize_market_family, normalize_sport_key
    from src.research.feature_control import ABLATION_NEVER_FEATURE_FIELDS, _all_safe_fields_for_combination
    from src.data.field_catalog import fields_for_model_mode
    from src.data.historical_sources import get_historical_data_source_rows
    from src.data.historical_odds import CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS, odds_to_implied_probability
    from src.data.line_movement import describe_line_movement_import_contract
    from src.data.source_event_links import describe_source_event_link_resolver
    from src.backtesting.dataset_builder import validate_paper_only_fixture_rows
    from src.backtesting.strategy_profiles import normalize_strategy_profile_key
    from src.backtesting.engine import run_backtesting_scaffold

    assert normalize_sport_key("nba") == "basketball_nba"
    assert normalize_market_family("moneyline") == "two_way_moneyline"
    assert evaluate_sport_feature_readiness(
        [{"sport": "nba", "event_date": "2024-01-01", "market": "moneyline", "selection": "home", "odds_at_decision_time": -110}],
        "nba",
    )["ok"]
    assert "final_result" in ABLATION_NEVER_FEATURE_FIELDS
    assert _all_safe_fields_for_combination("nba", "moneyline")
    assert fields_for_model_mode("one_0dte_options_trade")
    assert isinstance(get_historical_data_source_rows(), list)
    assert CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS
    assert odds_to_implied_probability(-110) > 0
    assert describe_line_movement_import_contract()
    assert describe_source_event_link_resolver()
    assert validate_paper_only_fixture_rows([])
    assert normalize_strategy_profile_key("all_sports") in {"all_sports", None}
    assert run_backtesting_scaffold([])["ok"]
