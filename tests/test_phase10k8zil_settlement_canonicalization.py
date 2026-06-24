from __future__ import annotations

import importlib
from pathlib import Path


def test_settlement_canonical_modules_import_and_delegate(tmp_path: Path) -> None:
    canonical = importlib.import_module("src.brokerage.settlement")
    service = importlib.import_module("src.services.settlement_service")
    rule_checker = importlib.import_module("automation_scheduler.settlement_rule_checker")
    discovery = importlib.import_module("automation_scheduler.settlement_discovery")

    assert canonical.compare_settlement_rules.__module__ == "src.brokerage.settlement"
    assert rule_checker.compare_settlement_rules.__module__ == "src.brokerage.settlement"
    assert discovery.classify_kalshi_settlement.__module__ == "src.services.settlement_service"
    assert discovery.build_outcome_completion_report.__module__ == "src.services.settlement_service"

    rule_sets = [
        {"includes_overtime": True, "void_on_push": False, "player_prop_settlement": "win", "prediction_resolution": "yes"},
        {"includes_overtime": True, "void_on_push": False, "player_prop_settlement": "win", "prediction_resolution": "yes"},
    ]
    assert rule_checker.compare_settlement_rules(rule_sets) == canonical.compare_settlement_rules(rule_sets)

    report = discovery.build_outcome_completion_report(
        pending_rows=[],
        imported_rows=[],
        read_only_records=[],
        use_kalshi_snapshot=False,
        base_data_dir=str(tmp_path),
    )
    assert report["status"] == "no_completion_candidates"
    assert report["completion_candidates_count"] == 0
    assert report["provider_write"] is False
    assert service.READ_ONLY_SETTLEMENT_SOURCE == "read_only_settlement"


def test_settlement_wrapper_files_still_exist() -> None:
    for relpath in [
        "automation_scheduler/settlement_rule_checker.py",
        "automation_scheduler/settlement_discovery.py",
        "src/brokerage/settlement.py",
        "src/services/settlement_service.py",
    ]:
        assert Path(relpath).exists(), relpath
