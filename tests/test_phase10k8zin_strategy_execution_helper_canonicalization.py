from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_strategy_execution_canonical_modules_import_and_delegate(tmp_path: Path) -> None:
    service = importlib.import_module("src.services.execution_service")

    assert service.score_broker_provider.__module__ == "src.services.execution_service"
    assert service.score_price_band.__module__ == "src.services.execution_service"
    assert service.detect_manifold_trap.__module__ == "src.services.execution_service"
    assert service.simulate_execution.__module__ == "src.services.execution_service"
    assert service.ExecutionDeskRejected.__module__ == "src.services.execution_service"

    assert service.build_broker_quality_report()["status"] == "ok"
    assert service.score_price_band(6)["price_band"] == "preferred_3_to_12"
    assert service.calculate_risk_reward(10, 9, 12)["risk_reward_permission_status"] == "VALID"
    assert (
        service.score_a_quality_setup(
            catalyst_quality_score=90,
            liquidity_quality_score=90,
            setup_quality_score=90,
            spread_quality_score=90,
            risk_quality_score=90,
            repeatability_score=90,
            track_record_support_score=90,
        )["a_quality_candidate"]
        is True
    )

    review = service.run_small_account_review(
        [
            {
                "asset_symbol": "ABC",
                "asset_type": "stock",
                "price": 6,
                "float_shares": 5_000_000,
                "daily_volume": 1_000_000,
                "relative_volume": 5,
                "intraday_percent_change": 12,
                "catalyst_detected": True,
                "catalyst_quality_score": 88,
            }
        ],
        persist_queue=False,
        base_data_dir=str(tmp_path),
    )
    assert review["ok"] is True
    assert review["provider_write"] is False
    assert review["review_queue_count"] >= 0

    trap = service.detect_manifold_trap(
        asset_type="stock",
        cluster_id="c1",
        cluster_name="demo",
        normalized_features={"confidence_score": 0.1},
        cluster_stats={"sample_size": 30, "insufficient_sample": False},
    )
    assert trap["provider_write"] is False
    assert trap["execution_allowed"] is False

    sim = service.simulate_execution(
        {"simulation_only": True, "candidate_id": "missing", "asset_class": "prediction_market"},
        records=[],
        persist=False,
        base_data_dir=str(tmp_path),
    )
    assert sim["status"] == "simulated"
    assert sim["execution_allowed"] is False
    assert sim["live_execution_enabled"] is False
    assert sim["simulation_only"] is True

    with pytest.raises(service.ExecutionDeskRejected):
        service.validate_simulation_request({"simulation_only": False})

    assert service.SAFETY_FLAGS["review_only"] is True


def test_strategy_execution_canonical_files_still_exist() -> None:
    for relpath in [
        "src/services/execution_service.py",
    ]:
        assert Path(relpath).exists(), relpath
