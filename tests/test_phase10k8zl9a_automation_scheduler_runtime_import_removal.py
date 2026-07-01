from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path


RUNTIME_FILES = [
    Path("main.py"),
    Path("streamlit_app.py"),
    Path("src/api/automation_review_outcomes_routes.py"),
    Path("src/api/provider_status_routes.py"),
    Path("src/brokerage/readiness.py"),
    Path("src/services/execution_service.py"),
    Path("src/services/ledger_service.py"),
    Path("src/services/settlement_service.py"),
]

EXPECTED_CANONICAL_IMPORTS = {
    "main.py": {"src.services.automation_scheduler_facade"},
    "streamlit_app.py": {"src.services.streamlit_dashboard_facade"},
    "src/api/automation_review_outcomes_routes.py": {"src.api.automation_security"},
    "src/api/provider_status_routes.py": {"src.services.automation_scheduler_facade"},
    "src/brokerage/readiness.py": {"src.brokerage.readiness_support"},
    "src/services/execution_service.py": {"src.services.execution_support"},
    "src/services/ledger_service.py": {"src.services.ledger_support"},
    "src/services/settlement_service.py": {"src.services.settlement_support"},
}

REPLACEMENT_MODULES = [
    "src.services.automation_scheduler_facade",
    "src.services.streamlit_dashboard_facade",
    "src.services.execution_support",
    "src.services.ledger_support",
    "src.services.settlement_support",
    "src.brokerage.readiness_support",
    "src.api.automation_security",
]


def _import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_phase10k8zl9a_runtime_import_removal():
    for path in RUNTIME_FILES:
        assert path.exists(), path
        modules = _import_modules(path)
        assert not any(
            module == "automation_scheduler" or module.startswith("automation_scheduler.")
            for module in modules
        ), f"direct scheduler import still present in {path}"
        expected = EXPECTED_CANONICAL_IMPORTS[path.as_posix()]
        assert modules.intersection(expected), f"canonical replacement missing in {path}"

    assert not Path("automation_scheduler").exists()
    assert not Path("src/automation_scheduler_legacy/__init__.py").exists()

    for module_name in REPLACEMENT_MODULES:
        module = import_module(module_name)
        assert module is not None

    facade = import_module("src.services.automation_scheduler_facade")
    assert hasattr(facade, "get_runtime_data_path")
    assert hasattr(facade, "get_automation_data_dir")

    dashboard = import_module("src.services.streamlit_dashboard_facade")
    assert hasattr(dashboard, "build_market_readiness_report")
    assert hasattr(dashboard, "DATA_LIBRARY_PATHS")

    execution_support = import_module("src.services.execution_support")
    assert hasattr(execution_support, "build_pattern_review_item")
    assert hasattr(execution_support, "persist_pattern_review_queue")

    ledger_support = import_module("src.services.ledger_support")
    assert hasattr(ledger_support, "SCHEMA_VERSION")
    assert hasattr(ledger_support, "normalize_event_type")

    settlement_support = import_module("src.services.settlement_support")
    assert hasattr(settlement_support, "PERSISTABLE_SOURCES")
    assert hasattr(settlement_support, "validate_outcome_record")

    readiness_support = import_module("src.brokerage.readiness_support")
    assert hasattr(readiness_support, "evaluate_owner_approval")
    assert hasattr(readiness_support, "EXECUTION_ATTEMPT_BLOCKED")

    security_module = import_module("src.api.automation_security")
    assert hasattr(security_module, "validate_cron_token")
