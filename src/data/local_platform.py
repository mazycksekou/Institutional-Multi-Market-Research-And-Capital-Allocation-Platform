from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections import Counter
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.analytics.model_governance.data_lineage import create_lineage_record
from src.data.data_paths import get_runtime_data_path
from src.data.local_loader import load_local_dataset
from src.data.validation import validate_dataset_rows
from src.storage.local_store import LocalStorageEngine, backend_available, create_local_storage_engine


LOCAL_DATA_PLATFORM_SCHEMA_VERSION = "src.data.local_platform.v1"
DEFAULT_LOCAL_PLATFORM_STORAGE_PATH = get_runtime_data_path("local_platform", "canonical_data.sqlite")
DEFAULT_LOCAL_PLATFORM_SOURCE_NAME = "local_synthetic_fixture"
DEFAULT_LOCAL_PLATFORM_PROVIDER = "local_fixture"
DEFAULT_LOCAL_PLATFORM_FEATURE_PACK = "local_feature_pack.v1"
DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY = "manual"
DEFAULT_LOCAL_PLATFORM_READINESS = "active"
DEFAULT_LOCAL_PLATFORM_OWNER = "local"
DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE = "fixture"
DEFAULT_LOCAL_PLATFORM_ASSET_CLASS = "mixed"
DEFAULT_LOCAL_PLATFORM_MARKET = "mixed"
DEFAULT_LOCAL_PLATFORM_MARKET_TYPE = "mixed"

RAW_VALUE_FIELDS = {
    "record_id",
    "dataset_id",
    "dataset_name",
    "owner",
    "source_name",
    "source_type",
    "source",
    "market",
    "market_type",
    "sport",
    "asset_class",
    "provider",
    "schema_version",
    "feature_pack",
    "storage_location",
    "readiness",
    "update_frequency",
    "validation_state",
    "status",
    "snapshot_id",
    "lineage_id",
    "version_id",
    "quality_score",
    "created_at",
    "updated_at",
    "timestamp",
    "event_id",
    "event_name",
    "price",
    "line",
    "odds",
    "implied_probability",
    "model_probability",
    "edge",
    "market_value",
}

NUMERIC_ROW_FIELDS = {
    "price",
    "line",
    "odds",
    "implied_probability",
    "model_probability",
    "edge",
    "quality_score",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return uuid.uuid5(uuid.NAMESPACE_URL, seed).hex


def _as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        if isinstance(obj, set):
            return sorted(obj)
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)

    return json.dumps(value, default=default, ensure_ascii=False, sort_keys=True)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        result = float(value)
        if result != result or result in (float("inf"), float("-inf")):
            return default
        return result
    except (TypeError, ValueError):
        return default


@dataclass(slots=True, frozen=True)
class DatasetContract:
    dataset_id: str
    dataset_name: str
    source_name: str = DEFAULT_LOCAL_PLATFORM_SOURCE_NAME
    source_type: str = DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE
    market: str = DEFAULT_LOCAL_PLATFORM_MARKET
    sport: str = ""
    asset_class: str = DEFAULT_LOCAL_PLATFORM_ASSET_CLASS
    provider: str = DEFAULT_LOCAL_PLATFORM_PROVIDER
    schema_version: str = LOCAL_DATA_PLATFORM_SCHEMA_VERSION
    feature_pack: str = DEFAULT_LOCAL_PLATFORM_FEATURE_PACK
    storage_location: str = ""
    readiness: str = DEFAULT_LOCAL_PLATFORM_READINESS
    update_frequency: str = DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY
    validation_state: str = "unknown"
    owner: str = DEFAULT_LOCAL_PLATFORM_OWNER
    status: str = "registered"
    market_type: str = DEFAULT_LOCAL_PLATFORM_MARKET_TYPE
    quality_score: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_id", _normalize_text(self.dataset_id))
        object.__setattr__(self, "dataset_name", _normalize_text(self.dataset_name))
        object.__setattr__(self, "source_name", _normalize_text(self.source_name, self.dataset_name))
        object.__setattr__(self, "source_type", _normalize_text(self.source_type, DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE).lower())
        object.__setattr__(self, "market", _normalize_text(self.market, DEFAULT_LOCAL_PLATFORM_MARKET))
        object.__setattr__(self, "sport", _normalize_text(self.sport))
        object.__setattr__(self, "asset_class", _normalize_text(self.asset_class, DEFAULT_LOCAL_PLATFORM_ASSET_CLASS))
        object.__setattr__(self, "provider", _normalize_text(self.provider, DEFAULT_LOCAL_PLATFORM_PROVIDER))
        object.__setattr__(self, "schema_version", _normalize_text(self.schema_version, LOCAL_DATA_PLATFORM_SCHEMA_VERSION))
        object.__setattr__(self, "feature_pack", _normalize_text(self.feature_pack, DEFAULT_LOCAL_PLATFORM_FEATURE_PACK))
        object.__setattr__(self, "storage_location", _normalize_text(self.storage_location))
        object.__setattr__(self, "readiness", _normalize_text(self.readiness, DEFAULT_LOCAL_PLATFORM_READINESS))
        object.__setattr__(self, "update_frequency", _normalize_text(self.update_frequency, DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY))
        object.__setattr__(self, "validation_state", _normalize_text(self.validation_state, "unknown"))
        object.__setattr__(self, "owner", _normalize_text(self.owner, DEFAULT_LOCAL_PLATFORM_OWNER))
        object.__setattr__(self, "status", _normalize_text(self.status, "registered"))
        object.__setattr__(self, "market_type", _normalize_text(self.market_type, DEFAULT_LOCAL_PLATFORM_MARKET_TYPE))
        object.__setattr__(self, "quality_score", _as_float(self.quality_score, 1.0))

    @classmethod
    def create(
        cls,
        dataset_name: str,
        *,
        dataset_id: str | None = None,
        source_name: str | None = None,
        source_type: str = DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE,
        market: str = DEFAULT_LOCAL_PLATFORM_MARKET,
        sport: str = "",
        asset_class: str = DEFAULT_LOCAL_PLATFORM_ASSET_CLASS,
        provider: str = DEFAULT_LOCAL_PLATFORM_PROVIDER,
        schema_version: str = LOCAL_DATA_PLATFORM_SCHEMA_VERSION,
        feature_pack: str = DEFAULT_LOCAL_PLATFORM_FEATURE_PACK,
        storage_location: str = "",
        readiness: str = DEFAULT_LOCAL_PLATFORM_READINESS,
        update_frequency: str = DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY,
        validation_state: str = "unknown",
        owner: str = DEFAULT_LOCAL_PLATFORM_OWNER,
        status: str = "registered",
        market_type: str = DEFAULT_LOCAL_PLATFORM_MARKET_TYPE,
        quality_score: float = 1.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> "DatasetContract":
        contract_id = dataset_id or _stable_id("dataset", dataset_name, market, sport, asset_class, provider)
        return cls(
            dataset_id=contract_id,
            dataset_name=dataset_name,
            source_name=source_name or dataset_name,
            source_type=source_type,
            market=market,
            sport=sport,
            asset_class=asset_class,
            provider=provider,
            schema_version=schema_version,
            feature_pack=feature_pack,
            storage_location=storage_location,
            readiness=readiness,
            update_frequency=update_frequency,
            validation_state=validation_state,
            owner=owner,
            status=status,
            market_type=market_type,
            quality_score=quality_score,
            metadata=metadata or {},
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DatasetContract":
        return cls.create(
            dataset_name=str(data.get("dataset_name") or data.get("name") or "local_dataset"),
            dataset_id=str(data.get("dataset_id") or "") or None,
            source_name=str(data.get("source_name") or data.get("source") or data.get("dataset_name") or "local_dataset"),
            source_type=str(data.get("source_type") or DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE),
            market=str(data.get("market") or DEFAULT_LOCAL_PLATFORM_MARKET),
            sport=str(data.get("sport") or ""),
            asset_class=str(data.get("asset_class") or DEFAULT_LOCAL_PLATFORM_ASSET_CLASS),
            provider=str(data.get("provider") or DEFAULT_LOCAL_PLATFORM_PROVIDER),
            schema_version=str(data.get("schema_version") or LOCAL_DATA_PLATFORM_SCHEMA_VERSION),
            feature_pack=str(data.get("feature_pack") or DEFAULT_LOCAL_PLATFORM_FEATURE_PACK),
            storage_location=str(data.get("storage_location") or ""),
            readiness=str(data.get("readiness") or DEFAULT_LOCAL_PLATFORM_READINESS),
            update_frequency=str(data.get("update_frequency") or DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY),
            validation_state=str(data.get("validation_state") or "unknown"),
            owner=str(data.get("owner") or DEFAULT_LOCAL_PLATFORM_OWNER),
            status=str(data.get("status") or "registered"),
            market_type=str(data.get("market_type") or DEFAULT_LOCAL_PLATFORM_MARKET_TYPE),
            quality_score=float(data.get("quality_score") or 1.0),
            metadata=dict(data.get("metadata") or {}),
        )

    def with_storage_location(self, storage_location: str) -> "DatasetContract":
        return replace(self, storage_location=_normalize_text(storage_location))

    def validation_payload(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "source_name": self.source_name,
            "source_type": self.source_type,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "market": self.market,
            "sport": self.sport,
            "asset_class": self.asset_class,
            "provider": self.provider,
            "schema_version": self.schema_version,
            "feature_pack": self.feature_pack,
            "storage_location": self.storage_location,
            "readiness": self.readiness,
            "update_frequency": self.update_frequency,
            "validation_state": self.validation_state,
            "owner": self.owner,
            "status": self.status,
            "market_type": self.market_type,
            "quality_score": self.quality_score,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class ValidationContract:
    required_fields: tuple[str, ...] = (
        "record_id",
        "dataset_id",
        "dataset_name",
        "source_name",
        "source_type",
        "timestamp",
        "schema_version",
        "version_id",
        "snapshot_id",
        "lineage_id",
        "market",
        "market_type",
        "asset_class",
        "provider",
        "quality_score",
    )
    unique_keys: tuple[str, ...] = ("record_id",)
    join_keys: tuple[str, ...] = ("dataset_id", "version_id")
    allowed_markets: tuple[str, ...] = ()
    allowed_sports: tuple[str, ...] = ()
    allowed_asset_classes: tuple[str, ...] = ()
    numeric_fields: tuple[str, ...] = ("quality_score", "price", "line", "odds", "implied_probability", "model_probability", "edge")

    def as_dict(self) -> dict[str, Any]:
        return {
            "required_fields": list(self.required_fields),
            "unique_keys": list(self.unique_keys),
            "join_keys": list(self.join_keys),
            "allowed_markets": list(self.allowed_markets),
            "allowed_sports": list(self.allowed_sports),
            "allowed_asset_classes": list(self.allowed_asset_classes),
            "numeric_fields": list(self.numeric_fields),
        }


def _coerce_rows(source: Any) -> list[dict[str, Any]]:
    if source is None:
        return []
    if isinstance(source, list):
        return [dict(row) for row in source if isinstance(row, Mapping)]
    if isinstance(source, tuple):
        return [dict(row) for row in source if isinstance(row, Mapping)]
    if isinstance(source, Mapping):
        for key in ("rows", "records", "items", "data"):
            nested = source.get(key)
            if isinstance(nested, list):
                return [dict(row) for row in nested if isinstance(row, Mapping)]
        return [dict(source)]
    return []


def load_rows_from_source(source: Any) -> list[dict[str, Any]]:
    if isinstance(source, (list, tuple)):
        return _coerce_rows(source)
    if isinstance(source, Mapping):
        backend = str(source.get("backend") or source.get("kind") or source.get("source_type") or "").strip().lower()
        if backend in {"sqlite", "duckdb"}:
            path = source.get("path") or source.get("database_path")
            query = str(source.get("query") or "").strip()
            table = str(source.get("table") or source.get("table_name") or "").strip()
            if not path:
                return []
            if backend == "sqlite":
                conn = sqlite3.connect(str(path))
                conn.row_factory = sqlite3.Row
                try:
                    if not query:
                        query = f"SELECT * FROM {table}" if table else "SELECT * FROM sqlite_master WHERE 0"
                    rows = conn.execute(query).fetchall()
                    return [dict(row) for row in rows]
                finally:
                    conn.close()
            if backend == "duckdb" and backend_available("duckdb"):
                conn = create_local_storage_engine(path, backend="duckdb")
                try:
                    if not query:
                        query = f"SELECT * FROM {table}" if table else "SELECT 1 WHERE FALSE"
                    return conn.query(query)
                finally:
                    conn.close()
        return _coerce_rows(source)
    path = Path(source)
    if path.exists():
        return load_local_dataset({"name": path.stem, "source_type": "local", "uri": str(path)}, path=path)
    return []


def _normalize_numeric(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_record(
    row: Mapping[str, Any],
    *,
    contract: DatasetContract,
    row_index: int,
    version_id: str,
    snapshot_id: str,
    lineage_id: str,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    payload = dict(row)
    record_id = _normalize_text(payload.get("record_id"), "") or _stable_id("record", contract.dataset_id, version_id, row_index)
    normalized: dict[str, Any] = {
        "record_id": record_id,
        "dataset_id": contract.dataset_id,
        "dataset_name": contract.dataset_name,
        "owner": payload.get("owner") or contract.owner,
        "source": payload.get("source") or contract.source_name,
        "source_name": payload.get("source_name") or contract.source_name,
        "source_type": payload.get("source_type") or contract.source_type,
        "market": payload.get("market") or contract.market,
        "market_type": payload.get("market_type") or contract.market_type,
        "sport": payload.get("sport") or contract.sport,
        "asset_class": payload.get("asset_class") or contract.asset_class,
        "provider": payload.get("provider") or contract.provider,
        "schema_version": payload.get("schema_version") or contract.schema_version,
        "feature_pack": payload.get("feature_pack") or contract.feature_pack,
        "storage_location": payload.get("storage_location") or contract.storage_location,
        "readiness": payload.get("readiness") or contract.readiness,
        "update_frequency": payload.get("update_frequency") or contract.update_frequency,
        "validation_state": payload.get("validation_state") or contract.validation_state,
        "status": payload.get("status") or contract.status,
        "snapshot_id": snapshot_id,
        "lineage_id": lineage_id,
        "version_id": version_id,
        "quality_score": _normalize_numeric(payload.get("quality_score")) or contract.quality_score,
        "created_at": payload.get("created_at") or created_at,
        "updated_at": payload.get("updated_at") or updated_at,
        "timestamp": payload.get("timestamp") or created_at,
        "event_id": payload.get("event_id"),
        "event_name": payload.get("event_name"),
        "price": _normalize_numeric(payload.get("price")),
        "line": _normalize_numeric(payload.get("line")),
        "odds": _normalize_numeric(payload.get("odds")),
        "implied_probability": _normalize_numeric(payload.get("implied_probability")),
        "model_probability": _normalize_numeric(payload.get("model_probability")),
        "edge": _normalize_numeric(payload.get("edge")),
        "market_value": payload.get("market_value"),
    }
    normalized["payload_json"] = _as_json(payload)
    return normalized


def normalize_dataset_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    contract: DatasetContract,
    version_id: str,
    snapshot_id: str,
    lineage_id: str,
    created_at: str | None = None,
    updated_at: str | None = None,
) -> list[dict[str, Any]]:
    created = created_at or utc_now_iso()
    updated = updated_at or created
    return [
        _normalize_record(
            row,
            contract=contract,
            row_index=index,
            version_id=version_id,
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            created_at=created,
            updated_at=updated,
        )
        for index, row in enumerate(rows)
    ]


def _validate_row_types(row: Mapping[str, Any], contract: ValidationContract) -> list[str]:
    warnings: list[str] = []
    for field in contract.numeric_fields:
        value = row.get(field)
        if value in (None, ""):
            continue
        if _normalize_numeric(value) is None:
            warnings.append(f"invalid_numeric:{field}")
    return warnings


def validate_rows_against_contract(
    rows: Sequence[Mapping[str, Any]],
    *,
    contract: DatasetContract,
    validation_contract: ValidationContract | None = None,
) -> dict[str, Any]:
    validation_contract = validation_contract or ValidationContract()
    base = validate_dataset_rows(rows, required_fields=validation_contract.required_fields)
    missing_rows = list(base.get("missing_rows", []))
    missing_fields = [field for row in missing_rows for field in row.get("missing_fields", [])]
    duplicate_ids: list[str] = []
    if "record_id" in validation_contract.unique_keys:
        seen: set[str] = set()
        for row in rows:
            record_id = _normalize_text(row.get("record_id"))
            if not record_id:
                continue
            if record_id in seen and record_id not in duplicate_ids:
                duplicate_ids.append(record_id)
            seen.add(record_id)
    market_issues: list[str] = []
    if validation_contract.allowed_markets:
        allowed_markets = {str(value).lower() for value in validation_contract.allowed_markets}
        for row in rows:
            market = _normalize_text(row.get("market")).lower()
            if market and market not in allowed_markets:
                market_issues.append(market)
    sport_issues: list[str] = []
    if validation_contract.allowed_sports:
        allowed_sports = {str(value).lower() for value in validation_contract.allowed_sports}
        for row in rows:
            sport = _normalize_text(row.get("sport")).lower()
            if sport and sport not in allowed_sports:
                sport_issues.append(sport)
    asset_issues: list[str] = []
    if validation_contract.allowed_asset_classes:
        allowed_asset_classes = {str(value).lower() for value in validation_contract.allowed_asset_classes}
        for row in rows:
            asset_class = _normalize_text(row.get("asset_class")).lower()
            if asset_class and asset_class not in allowed_asset_classes:
                asset_issues.append(asset_class)
    type_warnings = []
    for row in rows:
        type_warnings.extend(_validate_row_types(row, validation_contract))
    join_key_issues: list[str] = []
    for row in rows:
        for key in validation_contract.join_keys:
            if row.get(key) in (None, ""):
                join_key_issues.append(key)
    schema_mismatches = [row.get("schema_version") for row in rows if _normalize_text(row.get("schema_version")) not in {contract.schema_version, ""}]
    warnings = list(dict.fromkeys(type_warnings))
    errors = list(dict.fromkeys(
        [
            *missing_fields,
            *[f"duplicate:{value}" for value in duplicate_ids],
            *[f"market_incompatible:{value}" for value in market_issues],
            *[f"sport_incompatible:{value}" for value in sport_issues],
            *[f"asset_class_incompatible:{value}" for value in asset_issues],
            *[f"join_key_missing:{value}" for value in join_key_issues],
            *[f"schema_version_mismatch:{value}" for value in schema_mismatches if value not in (None, "")],
        ]
    ))
    ok = not errors
    return {
        "ok": ok,
        "status": "validated" if ok else "rejected",
        "dataset_id": contract.dataset_id,
        "dataset_name": contract.dataset_name,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "missing_fields": missing_fields,
        "duplicate_keys": duplicate_ids,
        "join_keys": join_key_issues,
        "market_issues": market_issues,
        "sport_issues": sport_issues,
        "asset_class_issues": asset_issues,
        "schema_version_issues": [value for value in schema_mismatches if value not in (None, "")],
        "warnings": warnings,
        "errors": errors,
        "validation_contract": validation_contract.as_dict(),
        "row_count": len(rows),
        "base_validation": base,
    }


def _row_base(contract: DatasetContract, *, version_id: str, snapshot_id: str, lineage_id: str, quality_score: float, created_at: str, updated_at: str) -> dict[str, Any]:
    return {
        "schema_version": contract.schema_version,
        "created_at": created_at,
        "updated_at": updated_at,
        "source": contract.source_name,
        "provider": contract.provider,
        "market": contract.market,
        "market_type": contract.market_type,
        "asset_class": contract.asset_class,
        "snapshot_id": snapshot_id,
        "lineage_id": lineage_id,
        "version_id": version_id,
        "quality_score": quality_score,
        "dataset_id": contract.dataset_id,
        "dataset_name": contract.dataset_name,
        "owner": contract.owner,
        "sport": contract.sport,
        "feature_pack": contract.feature_pack,
        "storage_location": contract.storage_location,
        "readiness": contract.readiness,
        "update_frequency": contract.update_frequency,
        "validation_state": contract.validation_state,
        "status": contract.status,
    }


def build_synthetic_local_dataset(
    record_count: int = 100,
    *,
    dataset_name: str = "synthetic_canonical_data_platform",
    dataset_id: str | None = None,
    storage_location: str | None = None,
) -> dict[str, Any]:
    count = max(1, int(record_count))
    storage_location = storage_location or str(DEFAULT_LOCAL_PLATFORM_STORAGE_PATH)
    contract = DatasetContract.create(
        dataset_name=dataset_name,
        dataset_id=dataset_id,
        source_name=DEFAULT_LOCAL_PLATFORM_SOURCE_NAME,
        source_type=DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE,
        market=DEFAULT_LOCAL_PLATFORM_MARKET,
        sport="",
        asset_class="mixed",
        provider=DEFAULT_LOCAL_PLATFORM_PROVIDER,
        schema_version=LOCAL_DATA_PLATFORM_SCHEMA_VERSION,
        feature_pack=DEFAULT_LOCAL_PLATFORM_FEATURE_PACK,
        storage_location=storage_location,
        readiness="scaffold",
        update_frequency=DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY,
        validation_state="pending",
        owner=DEFAULT_LOCAL_PLATFORM_OWNER,
        status="registered",
        market_type=DEFAULT_LOCAL_PLATFORM_MARKET_TYPE,
        quality_score=1.0,
        metadata={"fixture": True, "synthetic": True},
    ).with_storage_location(storage_location)

    market_groups = [
        ("soccer", "sports", "soccer", "goal_line"),
        ("basketball_nba", "sports", "basketball", "moneyline"),
        ("prediction_market", "prediction_market", "prediction_market", "yes_no"),
        ("stocks", "equity", "", "price"),
        ("options_0dte", "derivative", "", "0dte_call"),
    ]
    rows: list[dict[str, Any]] = []
    base_day = 1
    for index in range(count):
        market_name, asset_class, sport, market_type = market_groups[index % len(market_groups)]
        market_offset = index % len(market_groups)
        day = ((index % 28) + 1)
        timestamp = f"2024-01-{day:02d}T12:00:00Z"
        record_id = f"{contract.dataset_id}-row-{index:03d}"
        row = {
            "record_id": record_id,
            "dataset_id": contract.dataset_id,
            "dataset_name": contract.dataset_name,
            "owner": contract.owner,
            "source": contract.source_name,
            "source_name": contract.source_name,
            "source_type": contract.source_type,
            "market": market_name,
            "market_type": market_type,
            "sport": sport,
            "asset_class": asset_class,
            "provider": contract.provider,
            "schema_version": contract.schema_version,
            "feature_pack": contract.feature_pack,
            "storage_location": contract.storage_location,
            "readiness": contract.readiness,
            "update_frequency": contract.update_frequency,
            "validation_state": "pending",
            "status": "active",
            "timestamp": timestamp,
            "event_id": f"evt-{index:03d}",
            "event_name": f"Synthetic Event {index:03d}",
            "price": round(100 + index * 0.5 + market_offset, 2),
            "line": round(1.5 + (index % 7) * 0.25, 2),
            "odds": round(1.5 + (index % 5) * 0.1, 2),
            "implied_probability": round(0.4 + (index % 10) * 0.01, 4),
            "model_probability": round(0.42 + (index % 10) * 0.01, 4),
            "edge": round(0.02 + (index % 8) * 0.005, 4),
            "quality_score": 1.0,
        }
        rows.append(row)

    validation_contract = ValidationContract(
        allowed_markets=tuple(sorted({str(row["market"]).lower() for row in rows})),
        allowed_sports=tuple(sorted({str(row["sport"]).lower() for row in rows if row.get("sport")})),
        allowed_asset_classes=tuple(sorted({str(row["asset_class"]).lower() for row in rows})),
    )
    return {
        "dataset": contract,
        "rows": rows,
        "validation_contract": validation_contract,
    }


class LocalDataPlatform:
    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        backend: str = "sqlite",
        dataset_owner: str = DEFAULT_LOCAL_PLATFORM_OWNER,
    ) -> None:
        self.storage_path = Path(storage_path or DEFAULT_LOCAL_PLATFORM_STORAGE_PATH).expanduser().resolve()
        self.backend = str(backend or "sqlite").strip().lower()
        self.dataset_owner = _normalize_text(dataset_owner, DEFAULT_LOCAL_PLATFORM_OWNER)
        self.store = create_local_storage_engine(self.storage_path, backend=self.backend)
        self.store.ensure_schema()

    def _version_number(self, dataset_id: str) -> int:
        rows = self.store.fetch("dataset_versions", where="dataset_id = ?", params=[dataset_id], order_by="version_number ASC")
        return len(rows) + 1

    def _row_counts(self, dataset_id: str) -> dict[str, int]:
        counts = {
            "raw_record_count": self.store.count("raw_records") if self.store.table_exists("raw_records") else 0,
            "normalized_record_count": self.store.count("normalized_records") if self.store.table_exists("normalized_records") else 0,
            "feature_snapshot_count": self.store.count("feature_snapshots") if self.store.table_exists("feature_snapshots") else 0,
        }
        return counts

    def _dataset_payload(self, contract: DatasetContract, *, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = contract.as_dict()
        if extra:
            payload.update(dict(extra))
        payload["storage_path"] = str(self.storage_path)
        return payload

    def _registry_row(
        self,
        contract: DatasetContract,
        *,
        latest_version_number: int,
        latest_snapshot_id: str,
        latest_feature_snapshot_id: str,
        latest_validation_id: str,
        version_count: int,
        deprecated_at: str | None = None,
        deprecated_reason: str | None = None,
        validation_state: str | None = None,
    ) -> dict[str, Any]:
        created_at = utc_now_iso()
        payload = self._dataset_payload(
            contract,
            extra={
                "latest_version_number": latest_version_number,
                "latest_snapshot_id": latest_snapshot_id,
                "latest_feature_snapshot_id": latest_feature_snapshot_id,
                "latest_validation_id": latest_validation_id,
                "version_count": version_count,
                "deprecated_at": deprecated_at,
                "deprecated_reason": deprecated_reason,
                "validation_state": validation_state or contract.validation_state,
            },
        )
        return {
            **_row_base(
                contract,
                version_id=f"{contract.dataset_id}.registry",
                snapshot_id=latest_snapshot_id,
                lineage_id=f"{contract.dataset_id}.registry",
                quality_score=contract.quality_score,
                created_at=created_at,
                updated_at=created_at,
            ),
            "dataset_id": contract.dataset_id,
            "dataset_name": contract.dataset_name,
            "owner": contract.owner,
            "sport": contract.sport,
            "feature_pack": contract.feature_pack,
            "storage_location": contract.storage_location,
            "readiness": contract.readiness,
            "update_frequency": contract.update_frequency,
            "validation_state": validation_state or contract.validation_state,
            "status": contract.status,
            "latest_version_number": int(latest_version_number),
            "latest_snapshot_id": latest_snapshot_id,
            "latest_feature_snapshot_id": latest_feature_snapshot_id,
            "latest_validation_id": latest_validation_id,
            "version_count": int(version_count),
            "deprecated_at": deprecated_at,
            "deprecated_reason": deprecated_reason,
            "metadata_json": _as_json(dict(contract.metadata)),
            "payload_json": _as_json(payload),
        }

    def register_dataset(self, dataset: DatasetContract | Mapping[str, Any]) -> dict[str, Any]:
        contract = dataset if isinstance(dataset, DatasetContract) else DatasetContract.from_mapping(dataset)
        existing = self.read_dataset(contract.dataset_id)
        version_count = len(existing.get("versions", [])) if existing else 0
        latest_version_number = existing.get("latest_version_number", 0) if existing else 0
        latest_snapshot_id = existing.get("latest_snapshot_id") if existing else ""
        latest_feature_snapshot_id = existing.get("latest_feature_snapshot_id") if existing else ""
        latest_validation_id = existing.get("latest_validation_id") if existing else ""
        row = self._registry_row(
            contract,
            latest_version_number=latest_version_number,
            latest_snapshot_id=latest_snapshot_id or f"{contract.dataset_id}.snapshot.000",
            latest_feature_snapshot_id=latest_feature_snapshot_id or f"{contract.dataset_id}.feature.000",
            latest_validation_id=latest_validation_id or f"{contract.dataset_id}.validation.000",
            version_count=version_count,
            validation_state=contract.validation_state,
        )
        self.store.upsert("dataset_registry", row, key_columns=("dataset_id",))
        return row

    def update_dataset(self, dataset_id: str, **changes: Any) -> dict[str, Any]:
        current = self.read_dataset(dataset_id)
        if not current:
            raise KeyError(f"Unknown dataset_id: {dataset_id}")
        payload = dict(current["registry"])
        payload.update(changes)
        payload["dataset_id"] = dataset_id
        contract = DatasetContract.from_mapping(payload)
        return self.register_dataset(contract)

    def deprecate_dataset(self, dataset_id: str, *, reason: str = "deprecated") -> dict[str, Any]:
        current = self.read_dataset(dataset_id)
        if not current:
            raise KeyError(f"Unknown dataset_id: {dataset_id}")
        registry = current["registry"]
        contract = DatasetContract.from_mapping(registry)
        row = self._registry_row(
            replace(contract, status="deprecated", readiness="deprecated", validation_state="deprecated"),
            latest_version_number=int(registry.get("latest_version_number") or 0),
            latest_snapshot_id=str(registry.get("latest_snapshot_id") or f"{dataset_id}.snapshot.000"),
            latest_feature_snapshot_id=str(registry.get("latest_feature_snapshot_id") or f"{dataset_id}.feature.000"),
            latest_validation_id=str(registry.get("latest_validation_id") or f"{dataset_id}.validation.000"),
            version_count=int(registry.get("version_count") or 0),
            deprecated_at=utc_now_iso(),
            deprecated_reason=reason,
            validation_state="deprecated",
        )
        self.store.upsert("dataset_registry", row, key_columns=("dataset_id",))
        return row

    def validate_dataset(
        self,
        rows: Sequence[Mapping[str, Any]],
        contract: DatasetContract,
        validation_contract: ValidationContract | None = None,
    ) -> dict[str, Any]:
        return validate_rows_against_contract(rows, contract=contract, validation_contract=validation_contract)

    def store_validation_result(
        self,
        contract: DatasetContract,
        *,
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
        validation: Mapping[str, Any],
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> dict[str, Any]:
        now = created_at or utc_now_iso()
        payload = dict(validation)
        row = {
            **_row_base(
                contract,
                version_id=version_id,
                snapshot_id=snapshot_id,
                lineage_id=lineage_id,
                quality_score=1.0 if validation.get("ok") else 0.0,
                created_at=now,
                updated_at=updated_at or now,
            ),
            "status": "validated" if validation.get("ok") else "rejected",
            "validation_id": f"{version_id}.validation",
            "validation_passed": 1 if validation.get("ok") else 0,
            "error_count": int(validation.get("error_count") or 0),
            "warning_count": int(validation.get("warning_count") or 0),
            "missing_fields_json": _as_json(validation.get("missing_fields") or []),
            "duplicate_keys_json": _as_json(validation.get("duplicate_keys") or []),
            "join_keys_json": _as_json(validation.get("join_keys") or []),
            "validation_json": _as_json(payload),
            "payload_json": _as_json(payload),
        }
        self.store.upsert("validation_results", row, key_columns=("validation_id",))
        return row

    def version_dataset(
        self,
        contract: DatasetContract,
        *,
        raw_record_count: int,
        normalized_record_count: int,
        feature_snapshot_count: int,
        validation_id: str,
        snapshot_id: str,
        lineage_id: str,
        checksum: str,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        version_number = self._version_number(contract.dataset_id)
        version_id = f"{contract.dataset_id}.v{version_number:03d}"
        now = created_at or utc_now_iso()
        row = {
            **_row_base(
                contract,
                version_id=version_id,
                snapshot_id=snapshot_id,
                lineage_id=lineage_id,
                quality_score=contract.quality_score,
                created_at=now,
                updated_at=now,
            ),
            "version_id": version_id,
            "dataset_id": contract.dataset_id,
            "dataset_name": contract.dataset_name,
            "owner": contract.owner,
            "sport": contract.sport,
            "feature_pack": contract.feature_pack,
            "storage_location": contract.storage_location,
            "readiness": contract.readiness,
            "update_frequency": contract.update_frequency,
            "validation_state": contract.validation_state,
            "status": contract.status,
            "version_number": version_number,
            "raw_record_count": int(raw_record_count),
            "normalized_record_count": int(normalized_record_count),
            "feature_snapshot_count": int(feature_snapshot_count),
            "validation_id": validation_id,
            "checksum": checksum,
            "metadata_json": _as_json(dict(contract.metadata)),
            "payload_json": _as_json(
                {
                    **contract.as_dict(),
                    "version_number": version_number,
                    "raw_record_count": int(raw_record_count),
                    "normalized_record_count": int(normalized_record_count),
                    "feature_snapshot_count": int(feature_snapshot_count),
                    "validation_id": validation_id,
                    "checksum": checksum,
                }
            ),
        }
        self.store.upsert("dataset_versions", row, key_columns=("version_id",))
        return row

    def store_raw_records(
        self,
        contract: DatasetContract,
        rows: Sequence[Mapping[str, Any]],
        *,
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> list[dict[str, Any]]:
        now = created_at or utc_now_iso()
        updated = updated_at or now
        stored: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            payload = dict(row)
            record_id = _normalize_text(payload.get("record_id")) or _stable_id("raw_record", contract.dataset_id, version_id, index)
            stored_row = {
                **_row_base(
                    contract,
                    version_id=version_id,
                    snapshot_id=snapshot_id,
                    lineage_id=lineage_id,
                    quality_score=_as_float(payload.get("quality_score"), 1.0),
                    created_at=payload.get("created_at") or now,
                    updated_at=payload.get("updated_at") or updated,
                ),
                "record_id": record_id,
                "dataset_id": contract.dataset_id,
                "dataset_name": contract.dataset_name,
                "owner": payload.get("owner") or contract.owner,
                "sport": payload.get("sport") or contract.sport,
                "feature_pack": payload.get("feature_pack") or contract.feature_pack,
                "storage_location": payload.get("storage_location") or contract.storage_location,
                "readiness": payload.get("readiness") or contract.readiness,
                "update_frequency": payload.get("update_frequency") or contract.update_frequency,
                "validation_state": payload.get("validation_state") or contract.validation_state,
                "status": payload.get("status") or contract.status,
                "row_index": index,
                "payload_json": _as_json(payload),
            }
            self.store.upsert("raw_records", stored_row, key_columns=("record_id",))
            stored.append(stored_row)
        return stored

    def store_normalized_records(
        self,
        contract: DatasetContract,
        rows: Sequence[Mapping[str, Any]],
        *,
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> list[dict[str, Any]]:
        now = created_at or utc_now_iso()
        updated = updated_at or now
        stored: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            payload = dict(row)
            record_id = _normalize_text(payload.get("record_id")) or _stable_id("normalized_record", contract.dataset_id, version_id, index)
            stored_row = {
                **_row_base(
                    contract,
                    version_id=version_id,
                    snapshot_id=snapshot_id,
                    lineage_id=lineage_id,
                    quality_score=_as_float(payload.get("quality_score"), 1.0),
                    created_at=payload.get("created_at") or now,
                    updated_at=payload.get("updated_at") or updated,
                ),
                "record_id": record_id,
                "dataset_id": contract.dataset_id,
                "dataset_name": contract.dataset_name,
                "owner": payload.get("owner") or contract.owner,
                "sport": payload.get("sport") or contract.sport,
                "feature_pack": payload.get("feature_pack") or contract.feature_pack,
                "storage_location": payload.get("storage_location") or contract.storage_location,
                "readiness": payload.get("readiness") or contract.readiness,
                "update_frequency": payload.get("update_frequency") or contract.update_frequency,
                "validation_state": payload.get("validation_state") or contract.validation_state,
                "status": payload.get("status") or contract.status,
                "row_index": index,
                "raw_record_id": payload.get("raw_record_id") or payload.get("record_id") or _stable_id("raw_record", contract.dataset_id, version_id, index),
                "payload_json": _as_json(payload),
            }
            self.store.insert("normalized_records", stored_row)
            stored.append(stored_row)
        return stored

    def store_feature_snapshot(
        self,
        contract: DatasetContract,
        rows: Sequence[Mapping[str, Any]],
        *,
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> dict[str, Any]:
        now = created_at or utc_now_iso()
        updated = updated_at or now
        feature_values = [
            {
                key: row.get(key)
                for key in (
                    "record_id",
                    "timestamp",
                    "market",
                    "market_type",
                    "sport",
                    "asset_class",
                    "provider",
                    "price",
                    "line",
                    "odds",
                    "implied_probability",
                    "model_probability",
                    "edge",
                    "quality_score",
                )
                if key in row
            }
            for row in rows
        ]
        summary = {
            "record_count": len(feature_values),
            "market_counts": dict(Counter(str(row.get("market") or "unknown") for row in rows)),
            "sport_counts": dict(Counter(str(row.get("sport") or "unknown") for row in rows)),
            "asset_class_counts": dict(Counter(str(row.get("asset_class") or "unknown") for row in rows)),
        }
        row = {
            **_row_base(
                contract,
                version_id=version_id,
                snapshot_id=snapshot_id,
                lineage_id=lineage_id,
                quality_score=contract.quality_score,
                created_at=now,
                updated_at=updated,
            ),
            "snapshot_id": snapshot_id,
            "dataset_id": contract.dataset_id,
            "dataset_name": contract.dataset_name,
            "owner": contract.owner,
            "sport": contract.sport,
            "feature_pack": contract.feature_pack,
            "storage_location": contract.storage_location,
            "readiness": contract.readiness,
            "update_frequency": contract.update_frequency,
            "validation_state": contract.validation_state,
            "status": contract.status,
            "feature_pack_version": contract.feature_pack,
            "record_count": len(feature_values),
            "feature_count": len(feature_values[0]) if feature_values else 0,
            "feature_values_json": _as_json(feature_values),
            "summary_json": _as_json(summary),
            "payload_json": _as_json({"feature_values": feature_values, "summary": summary}),
        }
        self.store.upsert("feature_snapshots", row, key_columns=("snapshot_id",))
        return row

    def record_lineage(
        self,
        contract: DatasetContract,
        raw_rows: Sequence[Mapping[str, Any]],
        normalized_rows: Sequence[Mapping[str, Any]],
        *,
        version_id: str,
        snapshot_id: str,
        lineage_id: str,
        feature_snapshot_id: str,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> list[dict[str, Any]]:
        now = created_at or utc_now_iso()
        updated = updated_at or now
        edges: list[dict[str, Any]] = []
        for index, (raw_row, normalized_row) in enumerate(zip(raw_rows, normalized_rows, strict=False)):
            raw_record_id = _normalize_text(raw_row.get("record_id")) or _stable_id("raw_record", contract.dataset_id, version_id, index)
            normalized_record_id = _normalize_text(normalized_row.get("record_id")) or _stable_id("normalized_record", contract.dataset_id, version_id, index)
            raw_edge_payload = create_lineage_record(
                provider_id=contract.provider,
                provider_type=contract.asset_class or "dataset",
                payload_schema_version=contract.schema_version,
                snapshot_id=snapshot_id,
                source_type=contract.source_type,
                schema_version=LOCAL_DATA_PLATFORM_SCHEMA_VERSION,
                lineage_id=lineage_id,
                dataset_id=contract.dataset_id,
                dataset_name=contract.dataset_name,
                source_record_id=raw_record_id,
                target_record_id=normalized_record_id,
                source_stage="raw",
                target_stage="normalized",
                transformation="normalize_dataset_rows",
            )
            raw_edge = {
                **_row_base(
                    contract,
                    version_id=version_id,
                    snapshot_id=snapshot_id,
                    lineage_id=lineage_id,
                    quality_score=_as_float(normalized_row.get("quality_score"), 1.0),
                    created_at=now,
                    updated_at=updated,
                ),
                "lineage_edge_id": _stable_id("lineage_edge", contract.dataset_id, version_id, "raw", index),
                "source_stage": "raw",
                "source_id": raw_record_id,
                "target_stage": "normalized",
                "target_id": normalized_record_id,
                "transformation": "normalize_dataset_rows",
                "step_index": index * 2,
                "payload_json": _as_json(raw_edge_payload),
            }
            self.store.insert("lineage_edges", raw_edge)
            edges.append(raw_edge)

            feature_edge_payload = create_lineage_record(
                provider_id=contract.provider,
                provider_type=contract.asset_class or "dataset",
                payload_schema_version=contract.schema_version,
                snapshot_id=snapshot_id,
                source_type=contract.source_type,
                schema_version=LOCAL_DATA_PLATFORM_SCHEMA_VERSION,
                lineage_id=lineage_id,
                dataset_id=contract.dataset_id,
                dataset_name=contract.dataset_name,
                source_record_id=normalized_record_id,
                target_record_id=feature_snapshot_id,
                source_stage="normalized",
                target_stage="feature_snapshot",
                transformation="store_feature_snapshot",
            )
            feature_edge = {
                **_row_base(
                    contract,
                    version_id=version_id,
                    snapshot_id=snapshot_id,
                    lineage_id=lineage_id,
                    quality_score=_as_float(normalized_row.get("quality_score"), 1.0),
                    created_at=now,
                    updated_at=updated,
                ),
                "lineage_edge_id": _stable_id("lineage_edge", contract.dataset_id, version_id, "feature", index),
                "source_stage": "normalized",
                "source_id": normalized_record_id,
                "target_stage": "feature_snapshot",
                "target_id": feature_snapshot_id,
                "transformation": "store_feature_snapshot",
                "step_index": index * 2 + 1,
                "payload_json": _as_json(feature_edge_payload),
            }
            self.store.insert("lineage_edges", feature_edge)
            edges.append(feature_edge)
        return edges

    def ingest_dataset(
        self,
        source: Any,
        *,
        contract: DatasetContract | Mapping[str, Any] | None = None,
        validation_contract: ValidationContract | None = None,
        storage_location: str | None = None,
    ) -> dict[str, Any]:
        rows = load_rows_from_source(source)
        if not rows:
            return {
                "ok": False,
                "status": "missing_rows",
                "dataset": None,
                "validation": {"ok": False, "status": "missing_rows"},
                "storage": self.store.health(),
            }

        if contract is None:
            inferred = rows[0]
            dataset_name = str(
                inferred.get("dataset_name")
                or inferred.get("name")
                or inferred.get("source_name")
                or inferred.get("source")
                or "local_dataset"
            )
            contract = DatasetContract.create(
                dataset_name=dataset_name,
                source_name=str(inferred.get("source_name") or inferred.get("source") or dataset_name),
                source_type=str(inferred.get("source_type") or DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE),
                market=str(inferred.get("market") or DEFAULT_LOCAL_PLATFORM_MARKET),
                sport=str(inferred.get("sport") or ""),
                asset_class=str(inferred.get("asset_class") or DEFAULT_LOCAL_PLATFORM_ASSET_CLASS),
                provider=str(inferred.get("provider") or DEFAULT_LOCAL_PLATFORM_PROVIDER),
                schema_version=str(inferred.get("schema_version") or LOCAL_DATA_PLATFORM_SCHEMA_VERSION),
                feature_pack=str(inferred.get("feature_pack") or DEFAULT_LOCAL_PLATFORM_FEATURE_PACK),
                storage_location=storage_location or str(self.storage_path),
                readiness=str(inferred.get("readiness") or DEFAULT_LOCAL_PLATFORM_READINESS),
                update_frequency=str(inferred.get("update_frequency") or DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY),
                validation_state="pending",
                owner=str(inferred.get("owner") or self.dataset_owner),
                status="registered",
                market_type=str(inferred.get("market_type") or DEFAULT_LOCAL_PLATFORM_MARKET_TYPE),
                quality_score=float(inferred.get("quality_score") or 1.0),
                metadata=dict(inferred.get("metadata") or {}),
            )
        elif not isinstance(contract, DatasetContract):
            contract = DatasetContract.from_mapping(contract)
        if storage_location:
            contract = contract.with_storage_location(storage_location)
        elif not contract.storage_location:
            contract = contract.with_storage_location(str(self.storage_path))

        self.register_dataset(contract)

        created_at = utc_now_iso()
        snapshot_id = f"{contract.dataset_id}.snapshot.v{self._version_number(contract.dataset_id):03d}"
        lineage_id = f"{contract.dataset_id}.lineage.v{self._version_number(contract.dataset_id):03d}"
        normalized_rows = normalize_dataset_rows(
            rows,
            contract=contract,
            version_id=f"{contract.dataset_id}.v{self._version_number(contract.dataset_id):03d}",
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            created_at=created_at,
            updated_at=created_at,
        )

        validation = self.validate_dataset(normalized_rows, contract, validation_contract)
        validation_id = f"{contract.dataset_id}.validation.v{self._version_number(contract.dataset_id):03d}"
        validation_row = self.store_validation_result(
            replace(contract, validation_state="validated" if validation.get("ok") else "rejected"),
            version_id=f"{contract.dataset_id}.v{self._version_number(contract.dataset_id):03d}",
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            validation=validation,
            created_at=created_at,
            updated_at=created_at,
        )

        raw_rows = self.store_raw_records(
            contract,
            rows,
            version_id=f"{contract.dataset_id}.v{self._version_number(contract.dataset_id):03d}",
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            created_at=created_at,
            updated_at=created_at,
        )
        normalized_stored_rows = self.store_normalized_records(
            replace(contract, validation_state="validated" if validation.get("ok") else "rejected"),
            normalized_rows,
            version_id=f"{contract.dataset_id}.v{self._version_number(contract.dataset_id):03d}",
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            created_at=created_at,
            updated_at=created_at,
        )
        feature_snapshot = self.store_feature_snapshot(
            replace(contract, validation_state="validated" if validation.get("ok") else "rejected"),
            normalized_stored_rows,
            version_id=f"{contract.dataset_id}.v{self._version_number(contract.dataset_id):03d}",
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            created_at=created_at,
            updated_at=created_at,
        )
        self.record_lineage(
            contract,
            raw_rows,
            normalized_stored_rows,
            version_id=f"{contract.dataset_id}.v{self._version_number(contract.dataset_id):03d}",
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            feature_snapshot_id=feature_snapshot["snapshot_id"],
            created_at=created_at,
            updated_at=created_at,
        )

        checksum = hashlib.sha256(_as_json(normalized_stored_rows).encode("utf-8")).hexdigest()
        version_row = self.version_dataset(
            replace(contract, validation_state="validated" if validation.get("ok") else "rejected", status="active" if validation.get("ok") else "scaffold"),
            raw_record_count=len(raw_rows),
            normalized_record_count=len(normalized_stored_rows),
            feature_snapshot_count=1,
            validation_id=validation_row["validation_id"],
            snapshot_id=snapshot_id,
            lineage_id=lineage_id,
            checksum=checksum,
            created_at=created_at,
        )

        registry_row = self._registry_row(
            replace(contract, validation_state="validated" if validation.get("ok") else "rejected", status="active" if validation.get("ok") else "scaffold"),
            latest_version_number=int(version_row.get("version_number") or 0),
            latest_snapshot_id=snapshot_id,
            latest_feature_snapshot_id=feature_snapshot["snapshot_id"],
            latest_validation_id=validation_row["validation_id"],
            version_count=self._version_number(contract.dataset_id),
            validation_state="validated" if validation.get("ok") else "rejected",
        )
        self.store.upsert("dataset_registry", registry_row, key_columns=("dataset_id",))

        return {
            "ok": bool(validation.get("ok")),
            "status": "ingested" if validation.get("ok") else "ingested_with_validation_errors",
            "dataset": contract.as_dict(),
            "validation": validation,
            "registry": registry_row,
            "version": version_row,
            "validation_result": validation_row,
            "feature_snapshot": feature_snapshot,
            "raw_record_count": len(raw_rows),
            "normalized_record_count": len(normalized_stored_rows),
            "lineage_edge_count": len(raw_rows) * 2,
            "storage": self.store.health(),
        }

    def list_datasets(self) -> list[dict[str, Any]]:
        return self.store.fetch("dataset_registry", order_by="updated_at DESC, dataset_name ASC")

    def list_versions(self, dataset_id: str | None = None) -> list[dict[str, Any]]:
        if dataset_id:
            return self.store.fetch("dataset_versions", where="dataset_id = ?", params=[dataset_id], order_by="version_number ASC")
        return self.store.fetch("dataset_versions", order_by="created_at DESC")

    def list_validation_results(self, dataset_id: str | None = None) -> list[dict[str, Any]]:
        if dataset_id:
            return self.store.fetch("validation_results", where="dataset_id = ?", params=[dataset_id], order_by="created_at DESC")
        return self.store.fetch("validation_results", order_by="created_at DESC")

    def list_feature_snapshots(self, dataset_id: str | None = None) -> list[dict[str, Any]]:
        if dataset_id:
            return self.store.fetch("feature_snapshots", where="dataset_id = ?", params=[dataset_id], order_by="created_at DESC")
        return self.store.fetch("feature_snapshots", order_by="created_at DESC")

    def list_lineage_edges(self, dataset_id: str | None = None) -> list[dict[str, Any]]:
        if dataset_id:
            return self.store.fetch("lineage_edges", where="dataset_id = ?", params=[dataset_id], order_by="step_index ASC")
        return self.store.fetch("lineage_edges", order_by="created_at DESC")

    def read_dataset(self, dataset_id: str) -> dict[str, Any]:
        registry_rows = self.store.fetch("dataset_registry", where="dataset_id = ?", params=[dataset_id], limit=1)
        if not registry_rows:
            return {}
        registry = registry_rows[0]
        versions = self.list_versions(dataset_id)
        validations = self.list_validation_results(dataset_id)
        snapshots = self.list_feature_snapshots(dataset_id)
        lineage = self.list_lineage_edges(dataset_id)
        return {
            "registry": registry,
            "versions": versions,
            "validations": validations,
            "feature_snapshots": snapshots,
            "lineage_edges": lineage,
            "latest_version_number": int(registry.get("latest_version_number") or 0),
            "latest_snapshot_id": registry.get("latest_snapshot_id"),
            "latest_feature_snapshot_id": registry.get("latest_feature_snapshot_id"),
            "latest_validation_id": registry.get("latest_validation_id"),
        }

    def dashboard_snapshot(self, dataset_id: str | None = None) -> dict[str, Any]:
        datasets = self.list_datasets()
        if dataset_id is None and datasets:
            dataset_id = str(datasets[0].get("dataset_id") or "")
        selected = self.read_dataset(dataset_id) if dataset_id else {}
        lineage_edges = selected.get("lineage_edges") or []
        lineage_summary = {
            "edge_count": len(lineage_edges),
            "stages": dict(
                Counter(
                    f"{row.get('source_stage')}->{row.get('target_stage')}"
                    for row in lineage_edges
                )
            ),
        }
        validation_summary = selected.get("validations", [{}])[0] if selected.get("validations") else {}
        return {
            "ok": True,
            "status": "ok",
            "storage": self.store.health(),
            "datasets": datasets,
            "selected_dataset_id": dataset_id,
            "dataset_metadata": selected.get("registry"),
            "dataset_versions": selected.get("versions", []),
            "validation_summary": validation_summary,
            "feature_snapshots": selected.get("feature_snapshots", []),
            "lineage_summary": lineage_summary,
        }

    def close(self) -> None:
        self.store.close()


def create_local_platform(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    dataset_owner: str = DEFAULT_LOCAL_PLATFORM_OWNER,
) -> LocalDataPlatform:
    return LocalDataPlatform(storage_path=storage_path, backend=backend, dataset_owner=dataset_owner)


def build_local_platform_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    dataset_id: str | None = None,
    backend: str = "sqlite",
) -> dict[str, Any]:
    platform = create_local_platform(storage_path=storage_path, backend=backend)
    try:
        return platform.dashboard_snapshot(dataset_id)
    finally:
        platform.close()


__all__ = [
    "DEFAULT_LOCAL_PLATFORM_ASSET_CLASS",
    "DEFAULT_LOCAL_PLATFORM_FEATURE_PACK",
    "DEFAULT_LOCAL_PLATFORM_MARKET",
    "DEFAULT_LOCAL_PLATFORM_MARKET_TYPE",
    "DEFAULT_LOCAL_PLATFORM_OWNER",
    "DEFAULT_LOCAL_PLATFORM_PROVIDER",
    "DEFAULT_LOCAL_PLATFORM_READINESS",
    "DEFAULT_LOCAL_PLATFORM_SOURCE_NAME",
    "DEFAULT_LOCAL_PLATFORM_SOURCE_TYPE",
    "DEFAULT_LOCAL_PLATFORM_STORAGE_PATH",
    "DEFAULT_LOCAL_PLATFORM_UPDATE_FREQUENCY",
    "DatasetContract",
    "LocalDataPlatform",
    "LOCAL_DATA_PLATFORM_SCHEMA_VERSION",
    "ValidationContract",
    "backend_available",
    "build_local_platform_dashboard_snapshot",
    "build_synthetic_local_dataset",
    "create_local_platform",
    "load_rows_from_source",
    "normalize_dataset_rows",
    "validate_rows_against_contract",
]
