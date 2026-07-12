from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.research.experiment_registry import (
    EXPERIMENT_REGISTRY_SCHEMA_VERSION,
    ExperimentRegistryCorruptionError,
    ExperimentRecord,
    ExperimentRegistry,
    ExperimentRegistryIntegrityError,
    build_experiment_record,
    describe_experiment_registry,
    list_experiment_records,
    load_experiment_record,
    record_experiment,
)


FIXED_CREATED_AT = "2026-07-12T12:00:00Z"
GIT_COMMIT = "b49d5e673816002f067d6d6134967835fbf04ade"


def _parameter_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


def _base_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "experiment_name": "NFL baseline sweep",
        "git_commit": GIT_COMMIT,
        "dataset_version": "dataset.v1",
        "feature_registry_version": "feature.registry.v1",
        "feature_snapshot_version": "feature.snapshot.v1",
        "mathematical_engine_version": "math.engine.v1",
        "signal_version": "signal.v1",
        "decision_version": "decision.v1",
        "parameters": {"beta": 2, "alpha": 1},
        "status": "registered",
        "tags": ("nfl", "baseline", "nfl"),
        "notes": ("created for local validation", "reproducibility check"),
        "metrics_reference": {"uri": "data/metrics/exp-1.json"},
        "artifact_reference": "artifacts/exp-1.tar.gz",
        "created_at": FIXED_CREATED_AT,
    }
    kwargs.update(overrides)
    return kwargs


def test_build_experiment_record_records_versions_and_hash() -> None:
    record = build_experiment_record(**_base_kwargs())

    assert record.schema_version == EXPERIMENT_REGISTRY_SCHEMA_VERSION
    assert record.experiment_name == "NFL baseline sweep"
    assert record.status == "registered"
    assert record.tags == ("baseline", "nfl")
    assert record.notes == ("created for local validation", "reproducibility check")
    assert record.metrics_reference == {"uri": "data/metrics/exp-1.json"}
    assert record.artifact_reference == {"uri": "artifacts/exp-1.tar.gz"}
    assert record.parameter_hash == _parameter_hash({"alpha": 1, "beta": 2})
    assert record.experiment_id.startswith("exp_")
    assert len(record.experiment_id) == 28


def test_experiment_record_serializes_and_round_trips() -> None:
    record = build_experiment_record(**_base_kwargs())

    payload = record.as_dict()
    expected_json = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    assert payload["tags"] == ["baseline", "nfl"]
    assert payload["notes"] == ["created for local validation", "reproducibility check"]
    assert record.to_json() == expected_json
    assert json.loads(record.to_json()) == payload
    assert ExperimentRecord.from_dict(payload) == record
    assert ExperimentRecord.from_json(json.dumps(payload)) == record


def test_experiment_definition_identity_is_stable_without_run_attempt_fields() -> None:
    first = build_experiment_record(
        **_base_kwargs(parameters={"beta": 2, "alpha": 1}, tags=("nfl", "baseline"))
    )
    second = build_experiment_record(
        **_base_kwargs(parameters={"alpha": 1, "beta": 2}, tags=("baseline", "nfl"), created_at="2026-07-12T12:30:00Z", status="completed")
    )

    assert first.experiment_id == second.experiment_id
    assert first.parameter_hash == second.parameter_hash
    assert first.as_dict() != second.as_dict()


def test_registry_record_is_idempotent_for_identical_duplicate_writes(tmp_path: Path) -> None:
    registry = ExperimentRegistry(tmp_path)
    record = build_experiment_record(**_base_kwargs())

    stored = registry.record(record)
    duplicate = registry.record(build_experiment_record(**_base_kwargs()))
    record_path = tmp_path / f"{record.experiment_id}.json"

    assert duplicate == stored
    assert record_path.read_text(encoding="utf-8") == stored.to_json()
    assert registry.list() == [stored]


def test_registry_record_rejects_conflicting_duplicate_writes(tmp_path: Path) -> None:
    registry = ExperimentRegistry(tmp_path)
    record = build_experiment_record(**_base_kwargs())
    stored = registry.record(record)
    conflicting = build_experiment_record(
        **_base_kwargs(created_at="2026-07-12T12:30:00Z", status="completed")
    )

    with pytest.raises(ExperimentRegistryIntegrityError, match=record.experiment_id):
        registry.record(conflicting)

    assert registry.get(record.experiment_id) == stored
    assert registry.list() == [stored]


def test_experiment_record_is_frozen_and_registry_is_immutable(tmp_path: Path) -> None:
    registry = ExperimentRegistry(tmp_path)
    record = build_experiment_record(**_base_kwargs())
    stored = registry.record(record)
    record_path = tmp_path / f"{record.experiment_id}.json"

    with pytest.raises(FrozenInstanceError):
        stored.status = "completed"  # type: ignore[misc]

    assert record_path.read_text(encoding="utf-8") == stored.to_json()
    assert registry.get(record.experiment_id) == stored
    assert registry.list() == [stored]


@pytest.mark.parametrize(
    ("overrides", "error", "message"),
    [
        ({"experiment_name": " "}, ValueError, "experiment_name"),
        ({"git_commit": ""}, ValueError, "git_commit"),
        ({"parameters": ["not", "a", "mapping"]}, TypeError, "parameters"),
        ({"metrics_reference": ["not", "a", "mapping"]}, TypeError, "metrics_reference"),
    ],
)
def test_invalid_metadata_is_rejected(
    overrides: dict[str, object],
    error: type[Exception],
    message: str,
) -> None:
    kwargs = _base_kwargs(**overrides)

    with pytest.raises(error, match=message):
        build_experiment_record(**kwargs)


def test_registry_list_raises_on_malformed_json_and_supports_explicit_tolerance(tmp_path: Path) -> None:
    registry = ExperimentRegistry(tmp_path)
    record = build_experiment_record(**_base_kwargs())
    stored = registry.record(record)
    broken_path = tmp_path / "broken.json"
    broken_path.write_text("{\"experiment_id\": ", encoding="utf-8")

    with pytest.raises(ExperimentRegistryCorruptionError, match="broken.json"):
        registry.list()

    assert registry.list(strict=False) == [stored]


def test_registry_wrappers_round_trip_and_describe(tmp_path: Path) -> None:
    record = build_experiment_record(**_base_kwargs())
    stored = record_experiment(record, storage_dir=tmp_path)

    assert load_experiment_record(stored.experiment_id, storage_dir=tmp_path) == stored
    assert list_experiment_records(storage_dir=tmp_path) == [stored]

    summary = describe_experiment_registry(storage_dir=tmp_path)
    assert summary["schema_version"] == EXPERIMENT_REGISTRY_SCHEMA_VERSION
    assert summary["record_count"] == 1
    assert summary["experiment_ids"] == [stored.experiment_id]
