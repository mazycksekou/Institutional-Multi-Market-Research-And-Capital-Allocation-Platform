"""Canonical experiment registry for experiment definitions.

The registry records reproducibility metadata for an experiment definition,
not an individual execution attempt. A separate run identity will be added in
later phases if execution tracking becomes necessary.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from src.data.data_paths import get_runtime_data_path


EXPERIMENT_REGISTRY_SCHEMA_VERSION = "src.research.experiment_registry.v1"


class ExperimentRegistryError(RuntimeError):
    """Base error for experiment registry operations."""


class ExperimentRegistryIntegrityError(ExperimentRegistryError):
    """Raised when a duplicate experiment id has conflicting content."""

    def __init__(self, *, path: str | Path, experiment_id: str, message: str) -> None:
        super().__init__(f"{message}: {path}")
        self.path = str(path)
        self.experiment_id = experiment_id


class ExperimentRegistryCorruptionError(ExperimentRegistryError):
    """Raised when a stored experiment record cannot be parsed safely."""

    def __init__(self, *, path: str | Path, message: str, cause: Exception | None = None) -> None:
        super().__init__(f"{message}: {path}")
        self.path = str(path)
        self.cause = cause


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_text(value: Any, fallback: str = "") -> str:
    text = str(value if value is not None else fallback).strip()
    return text or fallback


def _json_ready(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {str(key): _json_ready(item) for key, item in asdict(value).items()}
    if hasattr(value, "as_dict"):
        return _json_ready(value.as_dict())
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, set):
        return [_json_ready(item) for item in sorted(value, key=lambda item: repr(item))]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return str(value)


def _canonical_json(value: Any) -> str:
    return json.dumps(_json_ready(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_iterable_values(value: Any, *, field_name: str, sort_unique: bool = False) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a string or iterable of strings, not a mapping")
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, Iterable):
        items = list(value)
    else:
        raise TypeError(f"{field_name} must be a string or iterable of strings")
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if sort_unique:
        cleaned = sorted(dict.fromkeys(cleaned))
    return tuple(cleaned)


def _normalize_reference(value: Any, *, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "as_dict"):
        payload = value.as_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        return {"uri": text}
    raise TypeError(f"{field_name} must be a mapping or string reference")


def _immutable_reference(value: Any, *, field_name: str) -> MappingProxyType:
    return MappingProxyType(_normalize_reference(value, field_name=field_name))


def _normalize_parameters(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError("parameters must be a mapping")
    return dict(value)


def _validate_required_text(value: Any, field_name: str) -> str:
    text = _normalize_text(value)
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _experiment_identity_payload(
    *,
    experiment_name: str,
    git_commit: str,
    dataset_version: str,
    feature_registry_version: str,
    feature_snapshot_version: str,
    mathematical_engine_version: str,
    signal_version: str,
    decision_version: str,
    parameter_hash: str,
) -> dict[str, str]:
    return {
        "experiment_name": experiment_name,
        "git_commit": git_commit,
        "dataset_version": dataset_version,
        "feature_registry_version": feature_registry_version,
        "feature_snapshot_version": feature_snapshot_version,
        "mathematical_engine_version": mathematical_engine_version,
        "signal_version": signal_version,
        "decision_version": decision_version,
        "parameter_hash": parameter_hash,
    }


def _expected_experiment_id(identity_payload: Mapping[str, Any]) -> str:
    return f"exp_{_stable_digest(identity_payload)[:24]}"


def get_default_experiment_registry_dir() -> Path:
    return get_runtime_data_path("experiment_registry")


@dataclass(slots=True, frozen=True)
class ExperimentRecord:
    experiment_id: str
    created_at: str
    git_commit: str
    dataset_version: str
    feature_registry_version: str
    feature_snapshot_version: str
    mathematical_engine_version: str
    signal_version: str
    decision_version: str
    parameter_hash: str
    experiment_name: str
    status: str = "planned"
    tags: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    metrics_reference: Mapping[str, Any] = field(default_factory=dict)
    artifact_reference: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = EXPERIMENT_REGISTRY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "experiment_id", _validate_required_text(self.experiment_id, "experiment_id"))
        object.__setattr__(self, "created_at", _validate_required_text(self.created_at, "created_at"))
        object.__setattr__(self, "git_commit", _validate_required_text(self.git_commit, "git_commit"))
        object.__setattr__(self, "dataset_version", _validate_required_text(self.dataset_version, "dataset_version"))
        object.__setattr__(self, "feature_registry_version", _validate_required_text(self.feature_registry_version, "feature_registry_version"))
        object.__setattr__(self, "feature_snapshot_version", _validate_required_text(self.feature_snapshot_version, "feature_snapshot_version"))
        object.__setattr__(self, "mathematical_engine_version", _validate_required_text(self.mathematical_engine_version, "mathematical_engine_version"))
        object.__setattr__(self, "signal_version", _validate_required_text(self.signal_version, "signal_version"))
        object.__setattr__(self, "decision_version", _validate_required_text(self.decision_version, "decision_version"))
        object.__setattr__(self, "parameter_hash", _validate_required_text(self.parameter_hash, "parameter_hash"))
        object.__setattr__(self, "experiment_name", _validate_required_text(self.experiment_name, "experiment_name"))
        object.__setattr__(self, "status", _validate_required_text(self.status, "status"))
        object.__setattr__(self, "tags", _normalize_iterable_values(self.tags, field_name="tags", sort_unique=True))
        object.__setattr__(self, "notes", _normalize_iterable_values(self.notes, field_name="notes"))
        object.__setattr__(self, "metrics_reference", _immutable_reference(self.metrics_reference, field_name="metrics_reference"))
        object.__setattr__(self, "artifact_reference", _immutable_reference(self.artifact_reference, field_name="artifact_reference"))
        object.__setattr__(self, "schema_version", _normalize_text(self.schema_version, EXPERIMENT_REGISTRY_SCHEMA_VERSION))

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "created_at": self.created_at,
            "git_commit": self.git_commit,
            "dataset_version": self.dataset_version,
            "feature_registry_version": self.feature_registry_version,
            "feature_snapshot_version": self.feature_snapshot_version,
            "mathematical_engine_version": self.mathematical_engine_version,
            "signal_version": self.signal_version,
            "decision_version": self.decision_version,
            "parameter_hash": self.parameter_hash,
            "experiment_name": self.experiment_name,
            "status": self.status,
            "tags": list(self.tags),
            "notes": list(self.notes),
            "metrics_reference": _json_ready(self.metrics_reference),
            "artifact_reference": _json_ready(self.artifact_reference),
            "schema_version": self.schema_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExperimentRecord":
        data = dict(payload)
        return cls(
            experiment_id=str(data.get("experiment_id", "")),
            created_at=str(data.get("created_at", "")),
            git_commit=str(data.get("git_commit", "")),
            dataset_version=str(data.get("dataset_version", "")),
            feature_registry_version=str(data.get("feature_registry_version", "")),
            feature_snapshot_version=str(data.get("feature_snapshot_version", "")),
            mathematical_engine_version=str(data.get("mathematical_engine_version", "")),
            signal_version=str(data.get("signal_version", "")),
            decision_version=str(data.get("decision_version", "")),
            parameter_hash=str(data.get("parameter_hash", "")),
            experiment_name=str(data.get("experiment_name", "")),
            status=str(data.get("status", "planned")),
            tags=data.get("tags") or (),
            notes=data.get("notes") or (),
            metrics_reference=data.get("metrics_reference") or {},
            artifact_reference=data.get("artifact_reference") or {},
            schema_version=str(data.get("schema_version", EXPERIMENT_REGISTRY_SCHEMA_VERSION)),
        )

    @classmethod
    def from_json(cls, text: str) -> "ExperimentRecord":
        return cls.from_dict(json.loads(text))


def build_experiment_record(
    *,
    experiment_name: str,
    git_commit: str,
    dataset_version: str,
    feature_registry_version: str,
    feature_snapshot_version: str,
    mathematical_engine_version: str,
    signal_version: str,
    decision_version: str,
    parameters: Mapping[str, Any] | None = None,
    status: str = "planned",
    tags: Iterable[Any] | None = None,
    notes: Iterable[Any] | str | None = None,
    metrics_reference: Mapping[str, Any] | str | None = None,
    artifact_reference: Mapping[str, Any] | str | None = None,
    created_at: str | None = None,
    experiment_id: str | None = None,
) -> ExperimentRecord:
    """Build a deterministic experiment-definition record.

    The generated experiment_id represents the experiment definition only.
    Repeated execution attempts for the same definition must use a separate run
    identity in a later phase.
    """
    parameter_payload = _normalize_parameters(parameters)
    parameter_hash = _stable_digest(parameter_payload)
    experiment_name_value = _validate_required_text(experiment_name, "experiment_name")
    git_commit_value = _validate_required_text(git_commit, "git_commit")
    dataset_version_value = _validate_required_text(dataset_version, "dataset_version")
    feature_registry_version_value = _validate_required_text(feature_registry_version, "feature_registry_version")
    feature_snapshot_version_value = _validate_required_text(feature_snapshot_version, "feature_snapshot_version")
    mathematical_engine_version_value = _validate_required_text(mathematical_engine_version, "mathematical_engine_version")
    signal_version_value = _validate_required_text(signal_version, "signal_version")
    decision_version_value = _validate_required_text(decision_version, "decision_version")
    status_value = _validate_required_text(status, "status")
    identity_payload = _experiment_identity_payload(
        experiment_name=experiment_name_value,
        git_commit=git_commit_value,
        dataset_version=dataset_version_value,
        feature_registry_version=feature_registry_version_value,
        feature_snapshot_version=feature_snapshot_version_value,
        mathematical_engine_version=mathematical_engine_version_value,
        signal_version=signal_version_value,
        decision_version=decision_version_value,
        parameter_hash=parameter_hash,
    )
    generated_experiment_id = _expected_experiment_id(identity_payload)
    provided_experiment_id = _normalize_text(experiment_id)
    if provided_experiment_id and provided_experiment_id != generated_experiment_id:
        raise ValueError("experiment_id does not match the deterministic experiment identity")
    return ExperimentRecord(
        experiment_id=generated_experiment_id,
        created_at=_normalize_text(created_at) or _utc_now_iso(),
        git_commit=git_commit_value,
        dataset_version=dataset_version_value,
        feature_registry_version=feature_registry_version_value,
        feature_snapshot_version=feature_snapshot_version_value,
        mathematical_engine_version=mathematical_engine_version_value,
        signal_version=signal_version_value,
        decision_version=decision_version_value,
        parameter_hash=parameter_hash,
        experiment_name=experiment_name_value,
        status=status_value,
        tags=tags or (),
        notes=notes or (),
        metrics_reference=metrics_reference or {},
        artifact_reference=artifact_reference or {},
    )


class ExperimentRegistry:
    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self._storage_dir = Path(storage_dir or get_default_experiment_registry_dir()).expanduser().resolve()
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def storage_dir(self) -> Path:
        return self._storage_dir

    def _record_path(self, experiment_id: str) -> Path:
        return self._storage_dir / f"{experiment_id}.json"

    def _write_json(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(payload), indent=2, sort_keys=True, ensure_ascii=False))

    def _load_json(self, path: Path) -> ExperimentRecord:
        try:
            return ExperimentRecord.from_json(path.read_text(encoding="utf-8"))
        except ExperimentRegistryError:
            raise
        except Exception as exc:
            raise ExperimentRegistryCorruptionError(
                path=path,
                message="malformed experiment registry file",
                cause=exc,
            ) from exc

    def record(self, record: ExperimentRecord) -> ExperimentRecord:
        if not isinstance(record, ExperimentRecord):
            raise TypeError("record must be an ExperimentRecord")
        expected_id = _expected_experiment_id(
            _experiment_identity_payload(
                experiment_name=record.experiment_name,
                git_commit=record.git_commit,
                dataset_version=record.dataset_version,
                feature_registry_version=record.feature_registry_version,
                feature_snapshot_version=record.feature_snapshot_version,
                mathematical_engine_version=record.mathematical_engine_version,
                signal_version=record.signal_version,
                decision_version=record.decision_version,
                parameter_hash=record.parameter_hash,
            )
        )
        payload = record.as_dict()
        if record.experiment_id != expected_id:
            raise ValueError("record experiment_id is not deterministic for the supplied metadata")

        path = self._record_path(record.experiment_id)
        if path.exists():
            existing = self._load_json(path)
            if existing.as_dict() == payload:
                return existing
            raise ExperimentRegistryIntegrityError(
                path=path,
                experiment_id=record.experiment_id,
                message="experiment registry already contains conflicting content",
            )

        try:
            self._write_json(path, payload)
        except FileExistsError:
            existing = self._load_json(path)
            if existing.as_dict() == payload:
                return existing
            raise ExperimentRegistryIntegrityError(
                path=path,
                experiment_id=record.experiment_id,
                message="experiment registry already contains conflicting content",
            )
        return record

    def get(self, experiment_id: str) -> ExperimentRecord | None:
        path = self._record_path(_normalize_text(experiment_id))
        if not path.exists():
            return None
        return self._load_json(path)

    def list(self, *, strict: bool = True) -> list[ExperimentRecord]:
        if not self._storage_dir.exists():
            return []
        records: list[ExperimentRecord] = []
        for path in sorted(self._storage_dir.glob("*.json")):
            try:
                records.append(self._load_json(path))
            except ExperimentRegistryCorruptionError:
                if strict:
                    raise
                continue
        records.sort(key=lambda record: (record.created_at, record.experiment_id))
        return records

    def describe(self, *, strict: bool = True) -> dict[str, Any]:
        records = self.list(strict=strict)
        return {
            "schema_version": EXPERIMENT_REGISTRY_SCHEMA_VERSION,
            "storage_dir": str(self._storage_dir),
            "record_count": len(records),
            "experiment_ids": [record.experiment_id for record in records],
        }


def record_experiment(record: ExperimentRecord, *, storage_dir: str | Path | None = None) -> ExperimentRecord:
    return ExperimentRegistry(storage_dir).record(record)


def load_experiment_record(experiment_id: str, *, storage_dir: str | Path | None = None) -> ExperimentRecord | None:
    return ExperimentRegistry(storage_dir).get(experiment_id)


def list_experiment_records(
    *, storage_dir: str | Path | None = None, strict: bool = True
) -> list[ExperimentRecord]:
    return ExperimentRegistry(storage_dir).list(strict=strict)


def describe_experiment_registry(
    *, storage_dir: str | Path | None = None, strict: bool = True
) -> dict[str, Any]:
    return ExperimentRegistry(storage_dir).describe(strict=strict)


__all__ = [
    "EXPERIMENT_REGISTRY_SCHEMA_VERSION",
    "ExperimentRegistryCorruptionError",
    "ExperimentRegistryError",
    "ExperimentRegistryIntegrityError",
    "ExperimentRecord",
    "ExperimentRegistry",
    "build_experiment_record",
    "describe_experiment_registry",
    "get_default_experiment_registry_dir",
    "list_experiment_records",
    "load_experiment_record",
    "record_experiment",
]
