from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.analytics.model_governance.data_lineage import create_lineage_record
from src.data.local_platform import (
    DatasetContract,
    LocalDataPlatform,
    ValidationContract,
    backend_available,
)
from src.data.market_profile_contracts import MarketProfileContract, validate_market_profile_contract
from src.data.market_profile_registry import get_market_profile
from src.data.data_paths import get_runtime_data_path


HISTORICAL_DATASET_ACQUISITION_RUNTIME_SCHEMA_VERSION = "src.data.historical_dataset_acquisition_runtime.v1"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_DATASET_NAME = "historical_raw_acquisition_cache"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_NAME = "historical_dataset_acquisition_runtime"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_TYPE = "raw_acquisition_cache"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_KEY = "historical_dataset_acquisition_runtime"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROVIDER = "repository"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_OWNER = "src.data"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_FEATURE_PACK = "historical_acquisition_runtime.v1"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET = "historical"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET_TYPE = "raw_acquisition_cache"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_ASSET_CLASS = "historical"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROFILE_ID = "sports:nfl"
DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_STORAGE_PATH = get_runtime_data_path(
    "historical_acquisition_runtime",
    "canonical_data.sqlite",
)


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, tuple):
            return list(obj)
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)

    return json.dumps(value, default=default, ensure_ascii=False, sort_keys=True)


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_iso(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _profile_slug(profile_id: str) -> str:
    slug = _normalize_text(profile_id).replace(":", ".").replace("/", ".").replace(" ", "_").lower()
    return slug or "unknown"


def _bundle_tables(source_bundle: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    tables = source_bundle.get("source_tables") or source_bundle.get("tables") or {}
    if not isinstance(tables, Mapping):
        return {}
    return {str(name): [dict(row) for row in rows if isinstance(row, Mapping)] for name, rows in tables.items()}


def _bundle_metadata(source_bundle: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "connector_id": _normalize_text(source_bundle.get("connector_id")),
        "connector_name": _normalize_text(source_bundle.get("connector_name")),
        "connector_role": _normalize_text(source_bundle.get("connector_role")),
        "execution_mode": _normalize_text(source_bundle.get("execution_mode")),
        "provider_role": _normalize_text(source_bundle.get("provider_role")),
        "source_family": _normalize_text(source_bundle.get("source_family")),
        "source_access_type": _normalize_text(source_bundle.get("source_access_type")),
        "provider_capability": dict(source_bundle.get("provider_capability") or {}),
        "field_provenance": dict(source_bundle.get("field_provenance") or {}),
    }


def _row_identifier(table_name: str, row: Mapping[str, Any], index: int) -> str:
    for key in (
        "record_id",
        "game_id",
        "result_id",
        "schedule_id",
        "odds_snapshot_id",
        "weather_snapshot_id",
        "team_stats_snapshot_id",
        "event_id",
        "market_id",
        "selection_id",
        "row_id",
    ):
        value = _normalize_text(row.get(key))
        if value:
            return value
    return f"{table_name}.{index:05d}"


def _row_checksum(row: Mapping[str, Any]) -> str:
    seed = _as_json(row)
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _build_raw_record(
    *,
    contract: "RawAcquisitionCacheContract",
    table_name: str,
    row: Mapping[str, Any],
    index: int,
    version_id: str,
    snapshot_id: str,
    lineage_id: str,
    created_at: str,
) -> dict[str, Any]:
    payload = dict(row)
    source_row_id = _row_identifier(table_name, payload, index)
    source_snapshot_time = _to_iso(
        payload.get("source_snapshot_time")
        or payload.get("snapshot_time")
        or payload.get("decision_time")
        or payload.get("timestamp")
        or created_at
    )
    acquisition_timestamp = _to_iso(payload.get("acquisition_timestamp") or contract.acquisition_timestamp or created_at)
    timestamp = _to_iso(payload.get("timestamp") or source_snapshot_time or acquisition_timestamp or created_at)
    checksum = payload.get("checksum") or _row_checksum(payload)
    provider_sources = list(contract.provider_sources)
    provider_versions = list(contract.provider_versions)
    source_metadata = {
        "source_name": contract.source_name,
        "source_type": contract.source_type,
        "source_key": contract.source_key,
        "provider": contract.provider,
        "provider_sources": provider_sources,
        "provider_versions": provider_versions,
        "source_bundle_id": contract.source_bundle_id,
        "source_table": table_name,
        "source_row_id": source_row_id,
        "source_snapshot_time": source_snapshot_time,
        "acquisition_timestamp": acquisition_timestamp,
        "connector_id": _normalize_text(contract.metadata.get("connector_id")),
        "connector_name": _normalize_text(contract.metadata.get("connector_name")),
        "connector_role": _normalize_text(contract.metadata.get("connector_role")),
        "execution_mode": _normalize_text(contract.metadata.get("execution_mode")),
        "provider_role": _normalize_text(contract.metadata.get("provider_role")),
        "provider_capability": dict(contract.metadata.get("provider_capability") or {}),
        "field_provenance": dict(contract.metadata.get("field_provenance") or {}),
    }
    lineage_payload = create_lineage_record(
        provider_id=contract.provider,
        provider_type=contract.profile_family or "historical",
        payload_schema_version=contract.schema_version,
        snapshot_id=snapshot_id,
        source_type=contract.source_type,
        schema_version=contract.schema_version,
        lineage_id=lineage_id,
        dataset_id=contract.dataset_id,
        dataset_name=contract.dataset_name,
        source_record_id=source_row_id,
        target_record_id=_stable_id("raw_acquisition_record", contract.dataset_id, version_id, table_name, source_row_id, index),
        source_stage="provider",
        target_stage="raw_acquisition_cache",
        transformation="stage_raw_acquisition_cache",
    )
    point_in_time_ok = not source_snapshot_time or not acquisition_timestamp or source_snapshot_time <= acquisition_timestamp
    record = {
        "record_id": _stable_id("raw_acquisition_record", contract.dataset_id, version_id, table_name, source_row_id, index),
        "dataset_id": contract.dataset_id,
        "dataset_name": contract.dataset_name,
        "owner": contract.owner,
        "source_name": contract.source_name,
        "source_type": contract.source_type,
        "source_key": contract.source_key,
        "source_table": table_name,
        "source_row_id": source_row_id,
        "source_bundle_id": contract.source_bundle_id,
        "market_profile": contract.market_profile,
        "profile_id": contract.profile_id,
        "profile_family": contract.profile_family,
        "market": contract.market,
        "market_type": contract.market_type,
        "asset_class": contract.asset_class,
        "provider": contract.provider,
        "provider_sources_json": _as_json(provider_sources),
        "provider_versions_json": _as_json(provider_versions),
        "timestamp": timestamp,
        "source_snapshot_time": source_snapshot_time,
        "acquisition_timestamp": acquisition_timestamp,
        "schema_version": contract.schema_version,
        "snapshot_id": snapshot_id,
        "lineage_id": lineage_id,
        "version_id": version_id,
        "quality_score": 1.0 if point_in_time_ok else 0.0,
        "completeness_score": 1.0,
        "point_in_time_status": "safe" if point_in_time_ok else "needs_review",
        "leakage_status": "none" if point_in_time_ok else "possible",
        "status": "cached" if point_in_time_ok else "review",
        "source_metadata_json": _as_json(source_metadata),
        "context_json": _as_json(
            {
                "profile": contract.profile_metadata,
                "table_name": table_name,
                "source_row_id": source_row_id,
            }
        ),
        "checksum": checksum,
        "payload_json": _as_json(payload),
        "lineage_record_json": _as_json(lineage_payload),
    }
    return record


@dataclass(slots=True, frozen=True)
class RawAcquisitionCacheContract:
    profile_id: str
    profile_family: str
    market_profile: str
    dataset_id: str
    dataset_name: str
    source_name: str
    source_type: str
    source_key: str
    provider: str
    provider_sources: tuple[str, ...]
    provider_versions: tuple[str, ...]
    source_bundle_id: str
    acquisition_timestamp: str
    market: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET
    market_type: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET_TYPE
    asset_class: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_ASSET_CLASS
    owner: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_OWNER
    schema_version: str = HISTORICAL_DATASET_ACQUISITION_RUNTIME_SCHEMA_VERSION
    feature_pack: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_FEATURE_PACK
    storage_location: str = ""
    readiness: str = "cache_ready"
    update_frequency: str = "manual"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _normalize_text(self.profile_id))
        object.__setattr__(self, "profile_family", _normalize_text(self.profile_family))
        object.__setattr__(self, "market_profile", _normalize_text(self.market_profile))
        object.__setattr__(self, "dataset_id", _normalize_text(self.dataset_id))
        object.__setattr__(self, "dataset_name", _normalize_text(self.dataset_name))
        object.__setattr__(self, "source_name", _normalize_text(self.source_name))
        object.__setattr__(self, "source_type", _normalize_text(self.source_type, DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_TYPE))
        object.__setattr__(self, "source_key", _normalize_text(self.source_key))
        object.__setattr__(self, "provider", _normalize_text(self.provider))
        object.__setattr__(self, "provider_sources", tuple(_normalize_text(value) for value in self.provider_sources if _normalize_text(value)))
        object.__setattr__(self, "provider_versions", tuple(_normalize_text(value) for value in self.provider_versions if _normalize_text(value)))
        object.__setattr__(self, "source_bundle_id", _normalize_text(self.source_bundle_id))
        object.__setattr__(self, "acquisition_timestamp", _to_iso(self.acquisition_timestamp))
        object.__setattr__(self, "market", _normalize_text(self.market, DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET))
        object.__setattr__(self, "market_type", _normalize_text(self.market_type, DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET_TYPE))
        object.__setattr__(self, "asset_class", _normalize_text(self.asset_class, DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_ASSET_CLASS))
        object.__setattr__(self, "owner", _normalize_text(self.owner, DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_OWNER))
        object.__setattr__(self, "schema_version", _normalize_text(self.schema_version, HISTORICAL_DATASET_ACQUISITION_RUNTIME_SCHEMA_VERSION))
        object.__setattr__(self, "feature_pack", _normalize_text(self.feature_pack, DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_FEATURE_PACK))
        object.__setattr__(self, "storage_location", _normalize_text(self.storage_location))
        object.__setattr__(self, "readiness", _normalize_text(self.readiness, "cache_ready"))
        object.__setattr__(self, "update_frequency", _normalize_text(self.update_frequency, "manual"))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def profile_metadata(self) -> dict[str, Any]:
        return dict(self.metadata)

    @classmethod
    def from_source_bundle(
        cls,
        *,
        profile: MarketProfileContract,
        source_bundle: Mapping[str, Any],
        storage_location: str,
        dataset_name: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_DATASET_NAME,
    ) -> "RawAcquisitionCacheContract":
        source_name = _normalize_text(source_bundle.get("source_name"), DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_NAME)
        source_type = _normalize_text(source_bundle.get("source_type"), DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_TYPE)
        source_key = _normalize_text(source_bundle.get("source_key"), DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_KEY)
        provider = _normalize_text(source_bundle.get("provider"), DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROVIDER)
        provider_sources = tuple(
            _normalize_text(value)
            for value in (source_bundle.get("provider_sources") or [source_name])
            if _normalize_text(value)
        )
        provider_versions = tuple(
            _normalize_text(value)
            for value in (source_bundle.get("provider_versions") or [source_bundle.get("provider_version") or source_bundle.get("dataset_version") or "v1"])
            if _normalize_text(value)
        )
        acquisition_timestamp = _to_iso(source_bundle.get("acquisition_timestamp") or source_bundle.get("created_at") or _utc_now_iso())
        slug = _profile_slug(profile.profile_id)
        dataset_id = _normalize_text(source_bundle.get("dataset_id"), f"dataset.{slug}.raw_acquisition_cache")
        source_bundle_id = _normalize_text(
            source_bundle.get("source_bundle_id"),
            _stable_id("raw_acquisition_bundle", profile.profile_id, source_name, source_type, source_key, acquisition_timestamp),
        )
        metadata = {
            "profile": profile.as_dict(),
            "source_tables": sorted(str(name) for name in _bundle_tables(source_bundle)),
            "source_bundle_id": source_bundle_id,
            "provider_sources": list(provider_sources),
            "provider_versions": list(provider_versions),
            "source_table_count": len(_bundle_tables(source_bundle)),
            "market_profile": profile.profile_id,
            "profile_id": profile.profile_id,
            "profile_family": profile.profile_family,
            **_bundle_metadata(source_bundle),
        }
        sport = _normalize_text(profile.metadata.get("sport") or profile.profile_family)
        return cls(
            profile_id=profile.profile_id,
            profile_family=profile.profile_family,
            market_profile=profile.profile_id,
            dataset_id=dataset_id,
            dataset_name=_normalize_text(dataset_name, DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_DATASET_NAME),
            source_name=source_name,
            source_type=source_type,
            source_key=source_key,
            provider=provider,
            provider_sources=provider_sources,
            provider_versions=provider_versions,
            source_bundle_id=source_bundle_id,
            acquisition_timestamp=acquisition_timestamp,
            market=profile.profile_id,
            market_type=DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET_TYPE,
            asset_class=profile.profile_family or DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_ASSET_CLASS,
            owner=DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_OWNER,
            storage_location=storage_location,
            readiness="cache_ready",
            update_frequency=_normalize_text(source_bundle.get("update_frequency"), "manual"),
            metadata={**metadata, "sport": sport},
        )

    def to_dataset_contract(self) -> DatasetContract:
        return DatasetContract.create(
            dataset_name=self.dataset_name,
            dataset_id=self.dataset_id,
            source_name=self.source_name,
            source_type=self.source_type,
            market=self.market_profile,
            sport=_normalize_text(self.metadata.get("sport") or self.profile_family),
            asset_class=self.asset_class,
            provider=self.provider,
            schema_version=self.schema_version,
            feature_pack=self.feature_pack,
            storage_location=self.storage_location,
            readiness=self.readiness,
            update_frequency=self.update_frequency,
            validation_state="validated",
            owner=self.owner,
            status="active",
            market_type=self.market_type,
            quality_score=1.0,
            metadata={
                **dict(self.metadata),
                "profile_id": self.profile_id,
                "profile_family": self.profile_family,
                "market_profile": self.market_profile,
                "source_bundle_id": self.source_bundle_id,
                "provider_sources": list(self.provider_sources),
                "provider_versions": list(self.provider_versions),
                "acquisition_timestamp": self.acquisition_timestamp,
            },
        ).with_storage_location(self.storage_location)

    def validation_contract(self) -> ValidationContract:
        return ValidationContract(
            required_fields=(
                "record_id",
                "dataset_id",
                "dataset_name",
                "source_name",
                "source_type",
                "source_key",
                "source_table",
                "source_row_id",
                "timestamp",
                "source_snapshot_time",
                "acquisition_timestamp",
                "schema_version",
                "version_id",
                "snapshot_id",
                "lineage_id",
                "market",
                "market_type",
                "asset_class",
                "provider",
                "quality_score",
                "checksum",
            ),
            unique_keys=("record_id",),
            join_keys=("dataset_id", "version_id", "source_table", "source_row_id"),
            allowed_markets=(self.market,),
            allowed_sports=(self.metadata.get("sport") or self.profile_family,),
            allowed_asset_classes=(self.asset_class,),
            numeric_fields=("quality_score",),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_family": self.profile_family,
            "market_profile": self.market_profile,
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "source_key": self.source_key,
            "provider": self.provider,
            "provider_sources": list(self.provider_sources),
            "provider_versions": list(self.provider_versions),
            "source_bundle_id": self.source_bundle_id,
            "acquisition_timestamp": self.acquisition_timestamp,
            "market": self.market,
            "market_type": self.market_type,
            "asset_class": self.asset_class,
            "owner": self.owner,
            "schema_version": self.schema_version,
            "feature_pack": self.feature_pack,
            "storage_location": self.storage_location,
            "readiness": self.readiness,
            "update_frequency": self.update_frequency,
            "metadata": dict(self.metadata),
        }


class HistoricalDatasetAcquisitionRuntime:
    """Reusable runtime owner for raw historical acquisition cache staging."""

    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        backend: str = "sqlite",
        dataset_owner: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_OWNER,
    ) -> None:
        self.storage_path = Path(storage_path or DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_STORAGE_PATH).expanduser().resolve()
        self.backend = str(backend or "sqlite").strip().lower()
        self.dataset_owner = _normalize_text(dataset_owner, DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_OWNER)
        self.platform = LocalDataPlatform(storage_path=self.storage_path, backend=self.backend, dataset_owner=self.dataset_owner)

    def close(self) -> None:
        self.platform.close()

    def __enter__(self) -> "HistoricalDatasetAcquisitionRuntime":
        _ = self.platform.store.connection
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def build_contract(
        self,
        *,
        profile_id: str,
        source_bundle: Mapping[str, Any],
        dataset_name: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_DATASET_NAME,
    ) -> RawAcquisitionCacheContract:
        profile = get_market_profile(profile_id)
        if profile is None:
            raise ValueError(f"Unknown market profile: {profile_id}")
        profile_validation = validate_market_profile_contract(profile)
        if not profile_validation.get("ok"):
            raise ValueError("; ".join(profile_validation.get("errors", [])) or f"invalid market profile: {profile_id}")
        return RawAcquisitionCacheContract.from_source_bundle(
            profile=profile,
            source_bundle=source_bundle,
            storage_location=str(self.storage_path),
            dataset_name=dataset_name,
        )

    def _source_rows(self, source_bundle: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
        return _bundle_tables(source_bundle)

    def _raw_records_for_bundle(
        self,
        *,
        contract: RawAcquisitionCacheContract,
        source_bundle: Mapping[str, Any],
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
        created_at: str,
    ) -> list[dict[str, Any]]:
        raw_rows: list[dict[str, Any]] = []
        for table_name, rows in sorted(self._source_rows(source_bundle).items()):
            for index, row in enumerate(rows):
                raw_rows.append(
                    _build_raw_record(
                        contract=contract,
                        table_name=table_name,
                        row=row,
                        index=index,
                        version_id=version_id,
                        snapshot_id=snapshot_id,
                        lineage_id=lineage_id,
                        created_at=created_at,
                    )
                )
        return raw_rows

    def stage_raw_acquisition_cache(
        self,
        source_bundle: Mapping[str, Any],
        *,
        profile_id: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROFILE_ID,
        dataset_name: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_DATASET_NAME,
    ) -> dict[str, Any]:
        contract = self.build_contract(profile_id=profile_id, source_bundle=source_bundle, dataset_name=dataset_name)
        dataset_contract = contract.to_dataset_contract()
        self.platform.register_dataset(dataset_contract)
        current = self.platform.read_dataset(contract.dataset_id)
        version_number = int(current.get("latest_version_number") or 0) + 1
        version_id = f"{contract.dataset_id}.v{version_number:03d}"
        snapshot_id = f"{contract.dataset_id}.snapshot.v{version_number:03d}"
        lineage_id = f"{contract.dataset_id}.lineage.v{version_number:03d}"
        created_at = _to_iso(source_bundle.get("acquisition_timestamp") or source_bundle.get("created_at") or contract.acquisition_timestamp or _utc_now_iso())
        raw_rows = self._raw_records_for_bundle(
            contract=contract,
            source_bundle=source_bundle,
            version_id=version_id,
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            created_at=created_at,
        )
        validation = self.platform.validate_dataset(
            raw_rows,
            contract.to_dataset_contract(),
            validation_contract=contract.validation_contract(),
        )
        validation_contract = replace(contract.to_dataset_contract(), validation_state="validated" if validation.get("ok") else "rejected")
        validation_row = self.platform.store_validation_result(
            validation_contract,
            version_id=version_id,
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            validation=validation,
            created_at=created_at,
            updated_at=created_at,
        )
        staged_raw_rows = self.platform.store_raw_records(
            validation_contract,
            raw_rows,
            version_id=version_id,
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            created_at=created_at,
            updated_at=created_at,
        )
        provider_row = self._provider_metadata_row(contract, source_bundle, created_at=created_at, version_id=version_id, snapshot_id=snapshot_id, lineage_id=lineage_id)
        if provider_row:
            self.platform.store.upsert("provider_metadata", provider_row, key_columns=("provider_id",))
        checksum = hashlib.sha256(_as_json(staged_raw_rows).encode("utf-8")).hexdigest()
        version_row = self.platform.version_dataset(
            validation_contract,
            raw_record_count=len(staged_raw_rows),
            normalized_record_count=0,
            feature_snapshot_count=0,
            validation_id=validation_row["validation_id"],
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            checksum=checksum,
            created_at=created_at,
        )
        registry_row = self.platform.register_dataset(validation_contract)
        lineage_edges: list[dict[str, Any]] = []
        for index, row in enumerate(staged_raw_rows):
            payload = json.loads(row.get("payload_json") or "{}")
            lineage_payload = json.loads(row.get("lineage_record_json") or "{}")
            lineage_edge = {
                "lineage_edge_id": _stable_id("raw_acquisition_lineage_edge", contract.dataset_id, version_id, index),
                "dataset_id": contract.dataset_id,
                "dataset_name": contract.dataset_name,
                "owner": contract.owner,
                "sport": validation_contract.sport,
                "feature_pack": validation_contract.feature_pack,
                "storage_location": validation_contract.storage_location,
                "readiness": validation_contract.readiness,
                "update_frequency": validation_contract.update_frequency,
                "validation_state": validation_contract.validation_state,
                "status": validation_contract.status,
                "source_stage": "provider",
                "source_id": _normalize_text(payload.get("source_row_id")) or _normalize_text(payload.get("record_id")),
                "target_stage": "raw_acquisition_cache",
                "target_id": _normalize_text(row.get("record_id")),
                "transformation": "stage_raw_acquisition_cache",
                "step_index": index,
                "payload_json": _as_json(lineage_payload),
            }
            self.platform.store.upsert(
                "lineage_edges",
                lineage_edge,
                key_columns=("lineage_edge_id",),
            )
            lineage_edges.append(lineage_edge)

        normalization_request = self.build_normalization_request(
            contract=contract,
            source_bundle=source_bundle,
            raw_rows=staged_raw_rows,
            validation=validation,
            version_id=version_id,
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            dataset_version=version_row["version_id"],
        )
        certification_request = self.build_certification_request(
            contract=contract,
            source_bundle=source_bundle,
            raw_rows=staged_raw_rows,
            validation=validation,
            version_id=version_id,
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            dataset_version=version_row["version_id"],
        )
        readiness_snapshot = self.build_readiness_snapshot(
            profile_id=profile_id,
            dataset_id=contract.dataset_id,
            source_bundle=source_bundle,
            normalization_request=normalization_request,
            certification_request=certification_request,
            validation=validation,
        )
        return {
            "ok": bool(validation.get("ok")),
            "status": "raw_cache_ready" if validation.get("ok") else "raw_cache_blocked",
            "contract": contract.as_dict(),
            "dataset_contract": validation_contract.as_dict(),
            "dataset_registry": registry_row,
            "dataset_version": version_row,
            "validation": validation,
            "validation_result": validation_row,
            "raw_record_count": len(staged_raw_rows),
            "raw_records": staged_raw_rows,
            "lineage_edges": lineage_edges,
            "normalization_request": normalization_request,
            "certification_request": certification_request,
            "source_bundle": dict(source_bundle),
            "provider_metadata": provider_row,
            "readiness_snapshot": readiness_snapshot,
        }

    def _provider_metadata_row(
        self,
        contract: RawAcquisitionCacheContract,
        source_bundle: Mapping[str, Any],
        *,
        created_at: str,
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
    ) -> dict[str, Any]:
        provider_capability = dict(source_bundle.get("provider_capability") or contract.metadata.get("provider_capability") or {})
        if not provider_capability and not _normalize_text(source_bundle.get("provider") or contract.provider):
            return {}
        provider_id = _normalize_text(provider_capability.get("provider_id") or source_bundle.get("provider") or contract.provider)
        provider_name = _normalize_text(provider_capability.get("provider_name") or source_bundle.get("source_name") or contract.source_name)
        provider_type = _normalize_text(
            provider_capability.get("provider_type")
            or provider_capability.get("provider_role")
            or source_bundle.get("source_type")
            or contract.source_type,
            DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_TYPE,
        )
        metadata = {
            "connector_id": _normalize_text(source_bundle.get("connector_id") or contract.metadata.get("connector_id")),
            "connector_name": _normalize_text(source_bundle.get("connector_name") or contract.metadata.get("connector_name")),
            "connector_role": _normalize_text(source_bundle.get("connector_role") or contract.metadata.get("connector_role")),
            "execution_mode": _normalize_text(source_bundle.get("execution_mode") or contract.metadata.get("execution_mode")),
            "provider_role": _normalize_text(provider_capability.get("provider_role") or source_bundle.get("provider_role") or contract.metadata.get("provider_role")),
            "provider_capability": provider_capability,
            "field_provenance": dict(source_bundle.get("field_provenance") or contract.metadata.get("field_provenance") or {}),
            "source_family": _normalize_text(source_bundle.get("source_family") or contract.metadata.get("source_family")),
            "source_access_type": _normalize_text(source_bundle.get("source_access_type") or contract.metadata.get("source_access_type")),
            "source_bundle_id": contract.source_bundle_id,
            "provider_sources": list(contract.provider_sources),
            "provider_versions": list(contract.provider_versions),
            "acquisition_timestamp": contract.acquisition_timestamp,
        }
        return {
            "schema_version": contract.schema_version,
            "created_at": created_at,
            "updated_at": created_at,
            "source": contract.source_name,
            "provider": provider_id,
            "market": contract.market_profile,
            "market_type": contract.market_type,
            "asset_class": contract.asset_class,
            "snapshot_id": snapshot_id,
            "lineage_id": lineage_id,
            "version_id": version_id,
            "quality_score": float(provider_capability.get("quality_score") or 1.0),
            "provider_id": provider_id,
            "provider_name": provider_name,
            "provider_type": provider_type,
            "contract_version": _normalize_text(provider_capability.get("contract_version") or contract.schema_version),
            "metadata_json": _as_json(metadata),
        }

    def build_normalization_request(
        self,
        *,
        contract: RawAcquisitionCacheContract,
        source_bundle: Mapping[str, Any],
        raw_rows: Sequence[Mapping[str, Any]],
        validation: Mapping[str, Any],
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
        dataset_version: str,
    ) -> dict[str, Any]:
        source_tables = self._source_rows(source_bundle)
        return {
            "ok": bool(validation.get("ok")),
            "status": "normalization_ready" if validation.get("ok") else "blocked",
            "dataset_id": contract.dataset_id,
            "dataset_name": contract.dataset_name,
            "dataset_version": dataset_version,
            "version_id": version_id,
            "snapshot_id": snapshot_id,
            "lineage_id": lineage_id,
            "profile_id": contract.profile_id,
            "profile_family": contract.profile_family,
            "market_profile": contract.market_profile,
            "source_bundle_id": contract.source_bundle_id,
            "raw_record_count": len(raw_rows),
            "source_table_names": sorted(source_tables),
            "source_table_counts": {name: len(rows) for name, rows in source_tables.items()},
            "target_tables": ["historical_events", "historical_markets", "historical_selections"],
            "source_bundle": dict(source_bundle),
            "validation": dict(validation),
            "notes": [
                "Normalization remains owned by the historical research database and domain dataset owners.",
                "This runtime only prepares the reusable handoff bundle.",
            ],
        }

    def build_certification_request(
        self,
        *,
        contract: RawAcquisitionCacheContract,
        source_bundle: Mapping[str, Any],
        raw_rows: Sequence[Mapping[str, Any]],
        validation: Mapping[str, Any],
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
        dataset_version: str,
    ) -> dict[str, Any]:
        return {
            "ok": bool(validation.get("ok")),
            "status": "certification_ready" if validation.get("ok") else "blocked",
            "dataset_id": contract.dataset_id,
            "dataset_name": contract.dataset_name,
            "dataset_version": dataset_version,
            "version_id": version_id,
            "snapshot_id": snapshot_id,
            "lineage_id": lineage_id,
            "profile_id": contract.profile_id,
            "profile_family": contract.profile_family,
            "market_profile": contract.market_profile,
            "source_bundle_id": contract.source_bundle_id,
            "raw_record_count": len(raw_rows),
            "source_bundle": dict(source_bundle),
            "validation": dict(validation),
            "certification_scope": "minimum certified historical schema",
            "notes": [
                "Certification remains owned by the historical research database.",
                "This runtime only prepares the certification handoff bundle.",
            ],
        }

    def build_readiness_snapshot(
        self,
        *,
        profile_id: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROFILE_ID,
        dataset_id: str | None = None,
        source_bundle: Mapping[str, Any] | None = None,
        normalization_request: Mapping[str, Any] | None = None,
        certification_request: Mapping[str, Any] | None = None,
        validation: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        profile = get_market_profile(profile_id)
        if profile is None:
            raise ValueError(f"Unknown market profile: {profile_id}")
        contract = self.build_contract(profile_id=profile_id, source_bundle=source_bundle or {}, dataset_name=DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_DATASET_NAME)
        selected_dataset_id = dataset_id or contract.dataset_id
        dataset_snapshot = self.platform.dashboard_snapshot(selected_dataset_id)
        raw_rows = self.platform.store.fetch(
            "raw_records",
            where="dataset_id = ?",
            params=[selected_dataset_id],
            order_by="row_index ASC",
        )
        validation_row = dataset_snapshot.get("validation_summary") or {}
        raw_ready = bool(raw_rows) and bool(validation_row)
        if validation is not None:
            raw_ready = bool(validation.get("ok")) and bool(raw_rows)
            validation_row = dict(validation)
        status = "ready" if raw_ready else "missing" if not raw_rows else "blocked"
        return {
            "ok": status == "ready",
            "status": status,
            "profile": profile.as_dict(),
            "contract": contract.as_dict(),
            "dataset_snapshot": dataset_snapshot,
            "raw_acquisition_cache": {
                "dataset_id": selected_dataset_id,
                "dataset_name": contract.dataset_name,
                "raw_record_count": len(raw_rows),
                "status": status,
                "validation": validation_row,
                "source_bundle_id": contract.source_bundle_id,
                "source_table_count": len(_bundle_tables(source_bundle or {})),
                "source_table_names": sorted(_bundle_tables(source_bundle or {})),
                "normalization_request": dict(normalization_request or {}),
                "certification_request": dict(certification_request or {}),
            },
            "readiness_summary": {
                "raw_record_count": len(raw_rows),
                "source_table_count": len(_bundle_tables(source_bundle or {})),
                "source_table_names": sorted(_bundle_tables(source_bundle or {})),
                "validation_ok": bool(validation_row.get("ok")) if isinstance(validation_row, Mapping) else False,
                "raw_acquisition_cache_status": status,
            },
        }

    def dashboard_snapshot(
        self,
        *,
        profile_id: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROFILE_ID,
        dataset_id: str | None = None,
        source_bundle: Mapping[str, Any] | None = None,
        normalization_request: Mapping[str, Any] | None = None,
        certification_request: Mapping[str, Any] | None = None,
        validation: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = self.build_readiness_snapshot(
            profile_id=profile_id,
            dataset_id=dataset_id,
            source_bundle=source_bundle,
            normalization_request=normalization_request,
            certification_request=certification_request,
            validation=validation,
        )
        dataset_snapshot = dict(snapshot.get("dataset_snapshot") or {})
        raw_acquisition_cache = dict(snapshot.get("raw_acquisition_cache") or {})
        snapshot["storage"] = dataset_snapshot.get("storage") or self.platform.store.health()
        snapshot["dataset_readiness"] = {
            "status": snapshot.get("status"),
            "ready_record_count": raw_acquisition_cache.get("raw_record_count", 0),
            "total_record_count": raw_acquisition_cache.get("raw_record_count", 0),
            "missing_records": [] if snapshot.get("ok") else ["raw_records"],
            "blocked_records": [] if snapshot.get("ok") else ["raw_records"],
            "raw_acquisition_cache": raw_acquisition_cache,
        }
        snapshot["readiness_summary"].update(
            {
                "dataset_status": dataset_snapshot.get("status"),
                "raw_acquisition_status": raw_acquisition_cache.get("status"),
            }
        )
        return snapshot


def build_historical_dataset_acquisition_runtime_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROFILE_ID,
    dataset_id: str | None = None,
    source_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    runtime = HistoricalDatasetAcquisitionRuntime(storage_path=storage_path, backend=backend)
    try:
        return runtime.dashboard_snapshot(
            profile_id=profile_id,
            dataset_id=dataset_id,
            source_bundle=source_bundle,
        )
    finally:
        runtime.close()


def get_historical_dataset_acquisition_runtime_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROFILE_ID,
    dataset_id: str | None = None,
    source_bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return build_historical_dataset_acquisition_runtime_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            profile_id=profile_id,
            dataset_id=dataset_id,
            source_bundle=source_bundle,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "historical_dataset_acquisition_runtime_snapshot_error",
            "storage": {},
            "dataset_snapshot": {},
            "raw_acquisition_cache": {},
            "readiness_summary": {},
            "warnings": [str(exc)],
        }


__all__ = [
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_ASSET_CLASS",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_DATASET_NAME",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_FEATURE_PACK",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_MARKET_TYPE",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_OWNER",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROFILE_ID",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_PROVIDER",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_KEY",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_NAME",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_SOURCE_TYPE",
    "DEFAULT_HISTORICAL_DATASET_ACQUISITION_RUNTIME_STORAGE_PATH",
    "HISTORICAL_DATASET_ACQUISITION_RUNTIME_SCHEMA_VERSION",
    "HistoricalDatasetAcquisitionRuntime",
    "RawAcquisitionCacheContract",
    "backend_available",
    "build_historical_dataset_acquisition_runtime_dashboard_snapshot",
    "get_historical_dataset_acquisition_runtime_snapshot_for_dashboard",
]
