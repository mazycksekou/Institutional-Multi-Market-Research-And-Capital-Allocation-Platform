from __future__ import annotations

import importlib
from pathlib import Path


def test_settlement_canonical_modules_import_and_delegate(tmp_path: Path) -> None:
    canonical = importlib.import_module("src.brokerage.settlement")
    service = importlib.import_module("src.services.settlement_service")

    assert canonical.compare_settlement_rules.__module__ == "src.brokerage.settlement"
    assert service.classify_kalshi_settlement.__module__ == "src.services.settlement_service"
    assert service.build_outcome_completion_report.__module__ == "src.services.settlement_service"

    rule_sets = [
        {"includes_overtime": True, "void_on_push": False, "player_prop_settlement": "win", "prediction_resolution": "yes"},
        {"includes_overtime": True, "void_on_push": False, "player_prop_settlement": "win", "prediction_resolution": "yes"},
    ]
    settlement_result = canonical.compare_settlement_rules(rule_sets)
    assert settlement_result["material_mismatch"] is False

    report = service.build_outcome_completion_report(
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


def test_settlement_canonical_files_still_exist() -> None:
    for relpath in [
        "src/brokerage/settlement.py",
        "src/services/settlement_service.py",
    ]:
        assert Path(relpath).exists(), relpath
