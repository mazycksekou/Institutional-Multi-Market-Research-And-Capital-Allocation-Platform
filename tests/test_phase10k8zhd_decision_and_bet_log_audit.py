from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHD_DECISION_AND_BET_LOG_AUDIT.md",
    ROOT / "DECISION_ENGINE_SERVICE_OWNERSHIP_AFTER_10K8ZHD.md",
    ROOT / "BET_LOG_MIGRATION_PLAN_AFTER_10K8ZHD.md",
]


def test_decision_and_bet_log_docs_state_the_boundary_split() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS).lower()
    for phrase in [
        "src/services/decision_engine.py",
        "bet_log.py",
        "bet_decision_engine.py",
        "service_orchestration_owner",
        "migrate_to_src_core",
        "compatibility_shim_candidate",
        "bet logging can remain root-level until a dedicated service/storage plan exists.",
    ]:
        assert phrase in text


def test_decision_engine_and_bet_log_modules_import_and_remain_local() -> None:
    decision_engine = importlib.import_module("src.services.decision_engine")
    bet_log = importlib.import_module("bet_log")
    bet_decision_engine = importlib.import_module("bet_decision_engine")

    summary = decision_engine.build_decision_summary({"american_odds": -110, "model_probability": 0.58, "market_probability": 0.54, "bankroll": 1000})
    assert summary["execution_enabled"] is False
    assert summary["live_connector_enabled"] is False

    entry = bet_log.create_bet_log_entry({"event": "demo", "selection": "home", "odds_american": -110, "stake": 25})
    assert entry["bet_id"]
    assert callable(bet_decision_engine.evaluate_lines_payload)


def test_bet_decision_engine_math_helpers_are_present() -> None:
    module = importlib.import_module("bet_decision_engine")
    for name in [
        "decision_label",
        "risk_grade_from_kelly",
        "kelly_fraction_multiplier",
        "no_vig_probability_for_line",
        "evaluate_lines_payload",
    ]:
        assert hasattr(module, name)
