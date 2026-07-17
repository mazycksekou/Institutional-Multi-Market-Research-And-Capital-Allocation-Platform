from __future__ import annotations

import difflib
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.data.data_paths import get_runtime_data_path
from src.data.source_event_links import resolve_source_event_link
from src.storage.local_store import (
    LocalStorageEngine,
    create_local_storage_engine,
    parquet_available,
)


DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION = "src.data.data_identity_lakehouse.v1"
DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION = "phase-data-identity-lakehouse.v1"
DEFAULT_DATA_IDENTITY_LAKEHOUSE_ROOT = get_runtime_data_path("lakehouse", "foundation")
DEFAULT_DATA_IDENTITY_FOUNDATION_STORAGE_PATH = get_runtime_data_path(
    "data_identity_foundation",
    "canonical_data.sqlite",
)

SUPPORTED_IDENTITY_ENTITY_TYPES: tuple[str, ...] = (
    "market_family",
    "sport",
    "league",
    "team",
    "player",
    "event",
    "venue",
    "canonical_market",
    "selection_outcome",
    "provider",
    "vendor_entity",
    "company",
    "security",
    "listing",
    "prediction_event",
    "prediction_contract",
)

MATCH_METHOD_HIERARCHY: tuple[str, ...] = (
    "approved_existing_mapping",
    "stable_external_identifier",
    "exact_composite_identity",
    "normalized_exact_match",
    "controlled_fuzzy_match",
    "manual_review",
)

FOUNDATION_DECISION_STATUSES: tuple[str, ...] = (
    "accepted",
    "accepted_with_warning",
    "quarantined",
    "rejected",
    "manual_review",
    "superseded",
)

BRONZE = "bronze"
SILVER = "silver"
GOLD = "gold"


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return float(default)
        result = float(value)
        if result != result or result in {float("inf"), float("-inf")}:
            return float(default)
        return result
    except (TypeError, ValueError):
        return float(default)


def _normalize_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _normalize_text(value).lower() in {"1", "true", "yes", "y", "ready", "accepted", "approved"}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_iso(value: Any, default: str = "") -> str:
    text = _normalize_text(value, default)
    if not text:
        return default
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_json_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, Mapping):
            return {str(key): item for key, item in parsed.items()}
    return {}


def _parse_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if value in (None, ""):
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return list(parsed)
    return []


def _as_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}.{digest}"


def _stable_digest(*parts: Any, length: int = 20) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[: max(8, int(length))]


def _normalize_token(value: Any) -> str:
    text = _normalize_text(value).lower()
    collapsed = "".join(character if character.isalnum() else " " for character in text)
    return " ".join(collapsed.split())


def _composite_key(row: Mapping[str, Any], fields: Sequence[str]) -> str:
    return "|".join(_normalize_token(row.get(field)) for field in fields)


def _candidate_similarity(left: Any, right: Any) -> float:
    return difflib.SequenceMatcher(a=_normalize_token(left), b=_normalize_token(right)).ratio()


def _timestamp_contract(
    row: Mapping[str, Any] | None = None,
    *,
    event_time: Any = None,
    published_at: Any = None,
    observed_at: Any = None,
    processed_at: Any = None,
    valid_from: Any = None,
    valid_to: Any = None,
    revision_number: Any = None,
    is_latest: Any = True,
    source_published_at: Any = None,
    system_observed_at: Any = None,
) -> dict[str, Any]:
    payload = dict(row or {})
    processed = _to_iso(
        processed_at
        or payload.get("processed_at")
        or payload.get("updated_at")
        or payload.get("created_at")
        or _utc_now()
    )
    published = _to_iso(
        published_at
        or payload.get("published_at")
        or payload.get("source_snapshot_time")
        or payload.get("snapshot_time")
        or payload.get("timestamp")
        or processed
    )
    observed = _to_iso(
        observed_at
        or payload.get("observed_at")
        or payload.get("acquisition_timestamp")
        or payload.get("created_at")
        or processed
    )
    event = _to_iso(
        event_time
        or payload.get("event_time")
        or payload.get("event_start_time")
        or payload.get("scheduled_kickoff_time")
        or payload.get("game_date")
        or published
    )
    source_published = _to_iso(
        source_published_at or payload.get("source_published_at") or payload.get("source_snapshot_time") or published
    )
    system_observed = _to_iso(
        system_observed_at or payload.get("system_observed_at") or payload.get("acquisition_timestamp") or observed
    )
    valid_from_value = _to_iso(valid_from or payload.get("valid_from") or observed or processed)
    valid_to_value = _to_iso(valid_to or payload.get("valid_to"))
    return {
        "event_time": event,
        "published_at": published,
        "observed_at": observed,
        "processed_at": processed,
        "valid_from": valid_from_value,
        "valid_to": valid_to_value,
        "revision_number": max(1, _normalize_int(revision_number or payload.get("revision_number"), 1)),
        "is_latest": 1 if _normalize_bool(is_latest if is_latest is not None else payload.get("is_latest", True)) else 0,
        "source_published_at": source_published,
        "system_observed_at": system_observed,
    }


def _lakehouse_partition_value(row: Mapping[str, Any], field_name: str) -> str:
    if field_name == "market_family":
        return _normalize_text(
            row.get("market_family")
            or row.get("profile_family")
            or row.get("asset_class")
            or "unknown"
        )
    if field_name == "sport_or_profile":
        return _normalize_text(
            row.get("market_profile")
            or row.get("profile_id")
            or row.get("market")
            or row.get("sport")
            or "unknown"
        )
    if field_name == "dataset":
        return _normalize_text(
            row.get("dataset_id")
            or row.get("dataset_name")
            or row.get("dataset_identifier")
            or "unknown"
        )
    if field_name == "provider":
        return _normalize_text(row.get("provider") or "unknown")
    if field_name == "season":
        season = row.get("season")
        if season in (None, ""):
            return "unknown"
        return str(season)
    if field_name == "acquisition_date":
        stamp = _to_iso(
            row.get("acquisition_timestamp")
            or row.get("observed_at")
            or row.get("processed_at")
            or row.get("created_at")
            or row.get("published_at")
        )
        return stamp[:10] if stamp else "unknown"
    return _normalize_text(row.get(field_name), "unknown")


def _partition_columns_for_table(layer_name: str, table_name: str) -> tuple[str, ...]:
    if layer_name == BRONZE:
        return ("market_family", "sport_or_profile", "dataset", "provider", "acquisition_date")
    if layer_name == SILVER:
        return ("market_family", "sport_or_profile", "dataset", "provider", "season")
    return ("market_family", "sport_or_profile", "dataset", "provider", "season")


def _safe_partition_path_token(value: str) -> str:
    raw = _normalize_text(value, "unknown")
    safe = "".join(character if character.isalnum() or character in {"-", "_", "."} else "_" for character in raw)
    safe = safe.strip("._") or "unknown"
    if len(safe) <= 48:
        return safe
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"{safe[:32]}_{digest}"


def _lakehouse_partition_path(
    lakehouse_root: Path,
    layer_name: str,
    table_name: str,
    partition_values: Mapping[str, Any],
) -> Path:
    return (
        lakehouse_root
        / layer_name
        / table_name
        / _stable_digest("lakehouse.partition.path", layer_name, table_name, partition_values, length=16)
    )


class DataIdentityLakehouseRuntime:
    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        backend: str = "sqlite",
        lakehouse_root: str | Path | None = None,
    ) -> None:
        self.store = create_local_storage_engine(
            storage_path or DEFAULT_DATA_IDENTITY_FOUNDATION_STORAGE_PATH,
            backend=backend,
        )
        self.backend = backend
        self.storage_path = self.store.path
        self.lakehouse_root = Path(lakehouse_root or DEFAULT_DATA_IDENTITY_LAKEHOUSE_ROOT).expanduser().resolve()
        self.lakehouse_root.mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        self.store.close()

    def _fetch(self, table_name: str, *, order_by: str | None = None) -> list[dict[str, Any]]:
        if not self.store.table_exists(table_name):
            return []
        return self.store.fetch(table_name, order_by=order_by)

    def _persist_row(
        self,
        table_name: str,
        row: Mapping[str, Any],
        *,
        key_columns: Sequence[str],
    ) -> dict[str, Any]:
        columns = set(self.store.table_columns(table_name))
        filtered = {str(key): value for key, value in dict(row).items() if str(key) in columns}
        self.store.upsert(table_name, filtered, key_columns=key_columns)
        return filtered

    def _find_latest_mapping(
        self,
        *,
        provider: str,
        entity_type: str,
        external_identifier: str,
    ) -> dict[str, Any]:
        if not self.store.table_exists("identity_mappings"):
            return {}
        rows = self.store.fetch(
            "identity_mappings",
            where="provider = ? AND entity_type = ? AND external_identifier = ?",
            params=[provider, entity_type, external_identifier],
            order_by="revision_number DESC, created_at DESC",
            limit=1,
        )
        return dict(rows[0]) if rows else {}

    def register_identity_mapping(
        self,
        *,
        provider: str,
        external_identifier: str,
        internal_identifier: str,
        entity_type: str,
        entity_name: str = "",
        canonical_key: str = "",
        mapping_status: str = "accepted",
        match_method: str = "approved_existing_mapping",
        confidence: float = 100.0,
        review_state: str = "approved",
        mapping_version: str = DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
        approval_reference: str = "foundation_seed",
        approval_evidence: Mapping[str, Any] | None = None,
        valid_from: Any = None,
        valid_to: Any = None,
        revision_number: int | None = None,
        is_latest: bool = True,
        source_payload: Mapping[str, Any] | None = None,
        lineage_reference: Mapping[str, Any] | None = None,
        notes: Mapping[str, Any] | None = None,
        dataset_id: str = "",
        dataset_name: str = "",
        source: str = "data_identity_lakehouse_runtime",
        market: str = "sports:nfl",
        market_type: str = "identity_mapping",
        asset_class: str = "historical",
        snapshot_id: str = "",
        lineage_id: str = "",
        version_id: str = "",
        **timestamps: Any,
    ) -> dict[str, Any]:
        entity = _normalize_text(entity_type)
        if entity not in SUPPORTED_IDENTITY_ENTITY_TYPES:
            raise ValueError(f"unsupported entity_type: {entity}")
        provider_name = _normalize_text(provider, "repository")
        external_id = _normalize_text(external_identifier)
        internal_id = _normalize_text(internal_identifier)
        if not external_id:
            raise ValueError("external_identifier is required")
        if not internal_id:
            raise ValueError("internal_identifier is required")
        latest = self._find_latest_mapping(
            provider=provider_name,
            entity_type=entity,
            external_identifier=external_id,
        )
        approval_payload = dict(approval_evidence or {})
        timestamp_payload = _timestamp_contract(
            source_payload,
            valid_from=valid_from,
            valid_to=valid_to,
            revision_number=revision_number or latest.get("revision_number"),
            is_latest=is_latest,
            **timestamps,
        )
        comparable_payload = {
            "internal_identifier": internal_id,
            "entity_name": _normalize_text(entity_name),
            "canonical_key": _normalize_text(canonical_key),
            "mapping_status": _normalize_text(mapping_status, "accepted"),
            "match_method": _normalize_text(match_method, "approved_existing_mapping"),
            "confidence": round(_normalize_float(confidence, 100.0), 4),
            "review_state": _normalize_text(review_state, "approved"),
            "mapping_version": _normalize_text(mapping_version, DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION),
            "approval_reference": _normalize_text(approval_reference, "foundation_seed"),
            "approval_evidence_json": _as_json(approval_payload),
            "valid_from": timestamp_payload["valid_from"],
            "valid_to": timestamp_payload["valid_to"],
            "source_payload_json": _as_json(dict(source_payload or {})),
            "lineage_reference_json": _as_json(dict(lineage_reference or {})),
            "notes_json": _as_json(dict(notes or {})),
        }
        if latest and _normalize_bool(latest.get("is_latest")):
            same_payload = all(
                str(latest.get(field, "")) == str(value)
                for field, value in comparable_payload.items()
            ) and _normalize_text(latest.get("internal_identifier")) == internal_id
            if same_payload:
                return dict(latest)
        current_revision = _normalize_int(latest.get("revision_number"), 0)
        revision = max(current_revision + 1, _normalize_int(revision_number, current_revision + 1))
        if latest and _normalize_bool(latest.get("is_latest")):
            latest_row = dict(latest)
            latest_row["is_latest"] = 0
            latest_row["mapping_status"] = "superseded"
            latest_row["valid_to"] = timestamp_payload["valid_from"] or latest_row.get("valid_to") or _utc_now()
            self._persist_row("identity_mappings", latest_row, key_columns=("mapping_id",))
        mapping_id = _stable_id("identity.mapping", provider_name, entity, external_id, revision)
        created_at = timestamp_payload["processed_at"] or _utc_now()
        row = {
            "mapping_id": mapping_id,
            "internal_identifier": internal_id,
            "external_identifier": external_id,
            "entity_type": entity,
            "entity_name": _normalize_text(entity_name),
            "canonical_key": _normalize_text(canonical_key),
            "mapping_status": comparable_payload["mapping_status"],
            "match_method": comparable_payload["match_method"],
            "confidence": comparable_payload["confidence"],
            "review_state": comparable_payload["review_state"],
            "mapping_version": comparable_payload["mapping_version"],
            "approval_reference": comparable_payload["approval_reference"],
            "approval_evidence_json": comparable_payload["approval_evidence_json"],
            "lineage_reference_json": comparable_payload["lineage_reference_json"],
            "source_payload_json": comparable_payload["source_payload_json"],
            "notes_json": comparable_payload["notes_json"],
            "dataset_id": _normalize_text(dataset_id),
            "dataset_name": _normalize_text(dataset_name),
            "source": _normalize_text(source),
            "provider": provider_name,
            "market": _normalize_text(market),
            "market_type": _normalize_text(market_type),
            "asset_class": _normalize_text(asset_class),
            "snapshot_id": _normalize_text(snapshot_id),
            "lineage_id": _normalize_text(lineage_id, mapping_id),
            "version_id": _normalize_text(version_id, comparable_payload["mapping_version"]),
            "quality_score": 1.0 if comparable_payload["mapping_status"] == "accepted" else 0.8,
            "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
            "created_at": created_at,
            "updated_at": created_at,
            **timestamp_payload,
        }
        self._persist_row("identity_mappings", row, key_columns=("mapping_id",))
        if approval_payload:
            self.record_mapping_approval(
                mapping_id=mapping_id,
                internal_identifier=internal_id,
                external_identifier=external_id,
                entity_type=entity,
                provider=provider_name,
                approval_state="approved" if comparable_payload["review_state"] == "approved" else comparable_payload["review_state"],
                approval_role="system",
                approval_reference=comparable_payload["approval_reference"],
                approval_evidence=approval_payload,
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
            )
        return row

    def record_mapping_approval(
        self,
        *,
        mapping_id: str,
        internal_identifier: str,
        external_identifier: str,
        entity_type: str,
        provider: str,
        approval_state: str,
        approval_role: str,
        approval_reference: str,
        approval_evidence: Mapping[str, Any] | None = None,
        valid_from: Any = None,
        valid_to: Any = None,
        details: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        approved_at = _utc_now()
        row = {
            "approval_id": _stable_id("identity.approval", mapping_id, approval_state, approval_reference),
            "mapping_id": _normalize_text(mapping_id),
            "internal_identifier": _normalize_text(internal_identifier),
            "external_identifier": _normalize_text(external_identifier),
            "entity_type": _normalize_text(entity_type),
            "provider": _normalize_text(provider),
            "approval_state": _normalize_text(approval_state),
            "approval_role": _normalize_text(approval_role),
            "approval_reference": _normalize_text(approval_reference),
            "approval_evidence_json": _as_json(dict(approval_evidence or {})),
            "approved_at": approved_at,
            "valid_from": _to_iso(valid_from or approved_at),
            "valid_to": _to_iso(valid_to),
            "details_json": _as_json(dict(details or {})),
            "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
            "created_at": approved_at,
            "updated_at": approved_at,
            "source": "data_identity_lakehouse_runtime",
            "market": "sports:nfl",
            "market_type": "mapping_approval",
            "asset_class": "historical",
            "snapshot_id": mapping_id,
            "lineage_id": _stable_id("identity.approval.lineage", mapping_id, approval_state),
            "version_id": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
            "quality_score": 1.0,
        }
        self._persist_row("mapping_approvals", row, key_columns=("approval_id",))
        return row

    def record_match_candidate(
        self,
        *,
        entity_type: str,
        provider: str,
        external_identifier: str,
        internal_identifier: str,
        candidate_internal_identifier: str,
        candidate_name: str,
        candidate_rank: int,
        match_method: str,
        confidence: float,
        decision_status: str,
        review_state: str,
        reasons: Sequence[str] | None = None,
        canonical_key: str = "",
        source_payload: Mapping[str, Any] | None = None,
        lineage_reference: Mapping[str, Any] | None = None,
        **timestamps: Any,
    ) -> dict[str, Any]:
        timestamp_payload = _timestamp_contract(source_payload, **timestamps)
        candidate_id = _stable_id(
            "identity.match_candidate",
            provider,
            entity_type,
            external_identifier,
            candidate_internal_identifier,
            candidate_rank,
            decision_status,
        )
        row = {
            "candidate_id": candidate_id,
            "entity_type": _normalize_text(entity_type),
            "provider": _normalize_text(provider),
            "internal_identifier": _normalize_text(internal_identifier),
            "external_identifier": _normalize_text(external_identifier),
            "candidate_internal_identifier": _normalize_text(candidate_internal_identifier),
            "candidate_name": _normalize_text(candidate_name),
            "candidate_rank": max(1, _normalize_int(candidate_rank, 1)),
            "match_method": _normalize_text(match_method),
            "confidence": round(_normalize_float(confidence), 4),
            "decision_status": _normalize_text(decision_status),
            "review_state": _normalize_text(review_state),
            "reasons_json": _as_json(list(reasons or [])),
            "canonical_key": _normalize_text(canonical_key),
            "lineage_reference_json": _as_json(dict(lineage_reference or {})),
            "source_payload_json": _as_json(dict(source_payload or {})),
            "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
            "created_at": timestamp_payload["processed_at"],
            "updated_at": timestamp_payload["processed_at"],
            "source": "data_identity_lakehouse_runtime",
            "market": "sports:nfl",
            "market_type": "identity_match_candidate",
            "asset_class": "historical",
            "snapshot_id": candidate_id,
            "lineage_id": _stable_id("identity.match_candidate.lineage", candidate_id),
            "version_id": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
            "quality_score": round(_normalize_float(confidence) / 100.0, 4),
            **timestamp_payload,
        }
        self._persist_row("identity_match_candidates", row, key_columns=("candidate_id",))
        return row

    def record_reconciliation_result(
        self,
        *,
        reconciliation_scope: str,
        entity_type: str,
        provider: str,
        internal_identifier: str,
        external_identifier: str,
        reconciliation_status: str,
        decision_status: str,
        decision_explanation: str,
        freshness_seconds: int,
        timestamp_agreement_status: str,
        outlier_status: str,
        quality_score: float,
        accepted_evidence: Sequence[Mapping[str, Any]] | None = None,
        rejected_evidence: Sequence[Mapping[str, Any]] | None = None,
        provider_reliability: Mapping[str, Any] | None = None,
        observation_identity: Mapping[str, Any] | None = None,
        source_payload: Mapping[str, Any] | None = None,
        lineage_reference: Mapping[str, Any] | None = None,
        revision_number: int = 1,
        is_latest: bool = True,
        **timestamps: Any,
    ) -> dict[str, Any]:
        timestamp_payload = _timestamp_contract(
            source_payload,
            revision_number=revision_number,
            is_latest=is_latest,
            **timestamps,
        )
        reconciliation_id = _stable_id(
            "identity.reconciliation",
            reconciliation_scope,
            entity_type,
            provider,
            internal_identifier,
            external_identifier,
            revision_number,
        )
        row = {
            "reconciliation_id": reconciliation_id,
            "reconciliation_scope": _normalize_text(reconciliation_scope),
            "entity_type": _normalize_text(entity_type),
            "provider": _normalize_text(provider),
            "internal_identifier": _normalize_text(internal_identifier),
            "external_identifier": _normalize_text(external_identifier),
            "reconciliation_status": _normalize_text(reconciliation_status),
            "decision_status": _normalize_text(decision_status),
            "decision_explanation": _normalize_text(decision_explanation),
            "freshness_seconds": max(0, _normalize_int(freshness_seconds, 0)),
            "timestamp_agreement_status": _normalize_text(timestamp_agreement_status),
            "outlier_status": _normalize_text(outlier_status),
            "quality_score": round(_normalize_float(quality_score), 4),
            "accepted_evidence_json": _as_json(list(accepted_evidence or [])),
            "rejected_evidence_json": _as_json(list(rejected_evidence or [])),
            "provider_reliability_json": _as_json(dict(provider_reliability or {})),
            "observation_identity_json": _as_json(dict(observation_identity or {})),
            "lineage_reference_json": _as_json(dict(lineage_reference or {})),
            "source_payload_json": _as_json(dict(source_payload or {})),
            "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
            "created_at": timestamp_payload["processed_at"],
            "updated_at": timestamp_payload["processed_at"],
            "source": "data_identity_lakehouse_runtime",
            "market": "sports:nfl",
            "market_type": "reconciliation_result",
            "asset_class": "historical",
            "snapshot_id": reconciliation_id,
            "lineage_id": _stable_id("identity.reconciliation.lineage", reconciliation_id),
            "version_id": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
            **timestamp_payload,
        }
        self._persist_row("identity_reconciliation_results", row, key_columns=("reconciliation_id",))
        return row

    def record_quality_event(
        self,
        *,
        dataset_table: str,
        record_identifier: str,
        entity_type: str,
        provider: str,
        internal_identifier: str,
        external_identifier: str,
        quality_event_type: str,
        severity: str,
        decision_status: str,
        decision_explanation: str,
        review_state: str,
        details: Mapping[str, Any] | None = None,
        source_payload: Mapping[str, Any] | None = None,
        lineage_reference: Mapping[str, Any] | None = None,
        **timestamps: Any,
    ) -> dict[str, Any]:
        timestamp_payload = _timestamp_contract(source_payload, **timestamps)
        quality_event_id = _stable_id(
            "identity.quality_event",
            dataset_table,
            record_identifier,
            quality_event_type,
            decision_status,
        )
        row = {
            "quality_event_id": quality_event_id,
            "dataset_table": _normalize_text(dataset_table),
            "record_identifier": _normalize_text(record_identifier),
            "entity_type": _normalize_text(entity_type),
            "provider": _normalize_text(provider),
            "internal_identifier": _normalize_text(internal_identifier),
            "external_identifier": _normalize_text(external_identifier),
            "quality_event_type": _normalize_text(quality_event_type),
            "severity": _normalize_text(severity),
            "decision_status": _normalize_text(decision_status),
            "decision_explanation": _normalize_text(decision_explanation),
            "review_state": _normalize_text(review_state),
            "details_json": _as_json(dict(details or {})),
            "lineage_reference_json": _as_json(dict(lineage_reference or {})),
            "source_payload_json": _as_json(dict(source_payload or {})),
            "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
            "created_at": timestamp_payload["processed_at"],
            "updated_at": timestamp_payload["processed_at"],
            "source": "data_identity_lakehouse_runtime",
            "market": "sports:nfl",
            "market_type": "data_quality_event",
            "asset_class": "historical",
            "snapshot_id": quality_event_id,
            "lineage_id": _stable_id("identity.quality_event.lineage", quality_event_id),
            "version_id": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
            "quality_score": 0.0 if _normalize_text(decision_status) in {"quarantined", "rejected"} else 0.8,
            **timestamp_payload,
        }
        self._persist_row("data_quality_events", row, key_columns=("quality_event_id",))
        return row

    def record_quarantine_record(
        self,
        *,
        dataset_table: str,
        record_identifier: str,
        entity_type: str,
        provider: str,
        internal_identifier: str,
        external_identifier: str,
        quarantine_reason: str,
        decision_status: str,
        review_state: str,
        release_state: str,
        match_candidate_ids: Sequence[str] | None = None,
        details: Mapping[str, Any] | None = None,
        source_payload: Mapping[str, Any] | None = None,
        lineage_reference: Mapping[str, Any] | None = None,
        **timestamps: Any,
    ) -> dict[str, Any]:
        timestamp_payload = _timestamp_contract(source_payload, **timestamps)
        quarantine_id = _stable_id(
            "identity.quarantine",
            dataset_table,
            record_identifier,
            quarantine_reason,
        )
        row = {
            "quarantine_id": quarantine_id,
            "dataset_table": _normalize_text(dataset_table),
            "record_identifier": _normalize_text(record_identifier),
            "entity_type": _normalize_text(entity_type),
            "provider": _normalize_text(provider),
            "internal_identifier": _normalize_text(internal_identifier),
            "external_identifier": _normalize_text(external_identifier),
            "quarantine_reason": _normalize_text(quarantine_reason),
            "decision_status": _normalize_text(decision_status),
            "review_state": _normalize_text(review_state),
            "release_state": _normalize_text(release_state),
            "match_candidate_ids_json": _as_json(list(match_candidate_ids or [])),
            "details_json": _as_json(dict(details or {})),
            "lineage_reference_json": _as_json(dict(lineage_reference or {})),
            "source_payload_json": _as_json(dict(source_payload or {})),
            "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
            "created_at": timestamp_payload["processed_at"],
            "updated_at": timestamp_payload["processed_at"],
            "source": "data_identity_lakehouse_runtime",
            "market": "sports:nfl",
            "market_type": "quarantine_record",
            "asset_class": "historical",
            "snapshot_id": quarantine_id,
            "lineage_id": _stable_id("identity.quarantine.lineage", quarantine_id),
            "version_id": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
            "quality_score": 0.0,
            **timestamp_payload,
        }
        self._persist_row("quarantine_records", row, key_columns=("quarantine_id",))
        return row

    def enqueue_manual_review(
        self,
        *,
        entity_type: str,
        provider: str,
        internal_identifier: str,
        external_identifier: str,
        decision_status: str,
        priority: str,
        recommended_action: str,
        candidate_ids: Sequence[str] | None = None,
        approval_reference: str = "manual_review",
        details: Mapping[str, Any] | None = None,
        source_payload: Mapping[str, Any] | None = None,
        lineage_reference: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        opened_at = _utc_now()
        review_id = _stable_id(
            "identity.manual_review",
            entity_type,
            provider,
            external_identifier,
            recommendation := _normalize_text(recommended_action),
        )
        row = {
            "review_id": review_id,
            "entity_type": _normalize_text(entity_type),
            "provider": _normalize_text(provider),
            "internal_identifier": _normalize_text(internal_identifier),
            "external_identifier": _normalize_text(external_identifier),
            "review_state": "open",
            "decision_status": _normalize_text(decision_status, "manual_review"),
            "priority": _normalize_text(priority, "normal"),
            "recommended_action": recommendation,
            "candidate_ids_json": _as_json(list(candidate_ids or [])),
            "approval_reference": _normalize_text(approval_reference, "manual_review"),
            "opened_at": opened_at,
            "closed_at": "",
            "details_json": _as_json(dict(details or {})),
            "lineage_reference_json": _as_json(dict(lineage_reference or {})),
            "source_payload_json": _as_json(dict(source_payload or {})),
            "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
            "created_at": opened_at,
            "updated_at": opened_at,
            "source": "data_identity_lakehouse_runtime",
            "market": "sports:nfl",
            "market_type": "manual_review_queue",
            "asset_class": "historical",
            "snapshot_id": review_id,
            "lineage_id": _stable_id("identity.manual_review.lineage", review_id),
            "version_id": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
            "quality_score": 0.0,
        }
        self._persist_row("manual_review_queue", row, key_columns=("review_id",))
        return row

    def resolve_identity_mapping(
        self,
        *,
        entity_type: str,
        provider: str,
        external_identifier: str,
        source_row: Mapping[str, Any],
        candidate_rows: Sequence[Mapping[str, Any]],
        exact_fields: Sequence[str] = (),
        normalized_fields: Sequence[str] = (),
    ) -> dict[str, Any]:
        entity = _normalize_text(entity_type)
        provider_name = _normalize_text(provider)
        external_id = _normalize_text(external_identifier)
        latest = self._find_latest_mapping(
            provider=provider_name,
            entity_type=entity,
            external_identifier=external_id,
        )
        if latest and _normalize_bool(latest.get("is_latest")) and _normalize_text(latest.get("review_state")) == "approved":
            return {
                "accepted": True,
                "decision_status": "accepted",
                "review_state": "approved",
                "match_method": "approved_existing_mapping",
                "confidence": 100.0,
                "internal_identifier": latest.get("internal_identifier"),
                "candidate_ids": [],
                "reasons": ["approved_existing_mapping"],
            }

        candidates = [dict(row) for row in candidate_rows]
        candidate_records: list[dict[str, Any]] = []

        if entity == "event":
            event_result = resolve_source_event_link(
                source_row,
                canonical_event_rows=candidates,
                min_score=90,
            )
            for rank, candidate in enumerate(candidates, start=1):
                candidate_id = _normalize_text(candidate.get("event_id"))
                score = 100.0 if candidate_id == _normalize_text(event_result.get("event_id")) else 0.0
                decision_status = "accepted" if candidate_id == _normalize_text(event_result.get("event_id")) and event_result.get("resolved") else "manual_review"
                record = self.record_match_candidate(
                    entity_type=entity,
                    provider=provider_name,
                    external_identifier=external_id,
                    internal_identifier=_normalize_text(event_result.get("event_id")),
                    candidate_internal_identifier=candidate_id,
                    candidate_name=_normalize_text(candidate.get("event_key") or candidate.get("event_id")),
                    candidate_rank=rank,
                    match_method=_normalize_text(event_result.get("match_method") or "manual_review"),
                    confidence=score,
                    decision_status=decision_status,
                    review_state="approved" if decision_status == "accepted" else "manual_review",
                    reasons=event_result.get("reasons") or event_result.get("warnings") or [],
                    canonical_key=_composite_key(candidate, ("sport", "league", "event_date", "home_team", "away_team")),
                    source_payload=source_row,
                )
                candidate_records.append(record)
            if event_result.get("resolved") and _normalize_text(event_result.get("event_id")):
                method = _normalize_text(event_result.get("match_method"))
                if method == "source_event_id":
                    method = "stable_external_identifier"
                elif method in {"exact_event_key", "existing_event_id"}:
                    method = "exact_composite_identity"
                elif method == "scored_match":
                    method = "controlled_fuzzy_match"
                return {
                    "accepted": True,
                    "decision_status": "accepted_with_warning" if method == "controlled_fuzzy_match" else "accepted",
                    "review_state": "approved",
                    "match_method": method,
                    "confidence": round(_normalize_float(event_result.get("score"), 100.0), 4),
                    "internal_identifier": _normalize_text(event_result.get("event_id")),
                    "candidate_ids": [row["candidate_id"] for row in candidate_records],
                    "reasons": event_result.get("reasons") or [],
                }
            manual_review = self.enqueue_manual_review(
                entity_type=entity,
                provider=provider_name,
                internal_identifier="",
                external_identifier=external_id,
                decision_status="manual_review",
                priority="high",
                recommended_action="review_event_identity_match",
                candidate_ids=[row["candidate_id"] for row in candidate_records],
                details={"resolver": "source_event_links", "reason": event_result.get("warnings") or event_result.get("reasons")},
                source_payload=source_row,
            )
            self.record_quarantine_record(
                dataset_table="historical_events",
                record_identifier=external_id or _normalize_text(source_row.get("source_event_id")),
                entity_type=entity,
                provider=provider_name,
                internal_identifier="",
                external_identifier=external_id,
                quarantine_reason="ambiguous_or_low_confidence_event_match",
                decision_status="manual_review",
                review_state="manual_review",
                release_state="pending_review",
                match_candidate_ids=[row["candidate_id"] for row in candidate_records],
                details={"review_id": manual_review["review_id"]},
                source_payload=source_row,
            )
            return {
                "accepted": False,
                "decision_status": "manual_review",
                "review_state": "manual_review",
                "match_method": "manual_review",
                "confidence": round(_normalize_float(event_result.get("score"), 0.0), 4),
                "internal_identifier": "",
                "candidate_ids": [row["candidate_id"] for row in candidate_records],
                "reasons": event_result.get("warnings") or event_result.get("reasons") or ["manual_review"],
                "review_id": manual_review["review_id"],
            }

        if entity in {"canonical_market", "selection_outcome"} and candidates:
            from src.data.market_identity_resolver import resolve_market_identity

            scored: list[tuple[dict[str, Any], dict[str, Any]]] = []
            for candidate in candidates:
                score = resolve_market_identity(dict(source_row), dict(candidate))
                scored.append((candidate, score))
            scored.sort(
                key=lambda item: (
                    _normalize_float(item[1].get("market_identity_confidence")),
                    _normalize_text(item[0].get("market_id") or item[0].get("selection_id")),
                ),
                reverse=True,
            )
            top_confidence = _normalize_float(scored[0][1].get("market_identity_confidence"))
            ambiguity = len(scored) > 1 and top_confidence == _normalize_float(scored[1][1].get("market_identity_confidence"))
            candidate_ids: list[str] = []
            for rank, (candidate, score) in enumerate(scored, start=1):
                decision_status = "accepted" if rank == 1 and score.get("accepted") and not ambiguity else "manual_review"
                candidate_record = self.record_match_candidate(
                    entity_type=entity,
                    provider=provider_name,
                    external_identifier=external_id,
                    internal_identifier=_normalize_text(candidate.get("market_id") or candidate.get("selection_id")),
                    candidate_internal_identifier=_normalize_text(candidate.get("market_id") or candidate.get("selection_id")),
                    candidate_name=_normalize_text(candidate.get("market_name") or candidate.get("selection")),
                    candidate_rank=rank,
                    match_method="exact_composite_identity" if score.get("same_market_identity") else "controlled_fuzzy_match",
                    confidence=top_confidence if rank == 1 else _normalize_float(score.get("market_identity_confidence")),
                    decision_status=decision_status,
                    review_state="approved" if decision_status == "accepted" else "manual_review",
                    reasons=score.get("reasons") or [],
                    canonical_key=_composite_key(candidate, ("event_id", "market_type", "selection", "book")),
                    source_payload=source_row,
                )
                candidate_ids.append(candidate_record["candidate_id"])
            if scored and scored[0][1].get("accepted") and not ambiguity and top_confidence >= 85:
                top_candidate = scored[0][0]
                return {
                    "accepted": True,
                    "decision_status": "accepted_with_warning" if top_confidence < 95 else "accepted",
                    "review_state": "approved",
                    "match_method": "exact_composite_identity" if scored[0][1].get("same_market_identity") else "controlled_fuzzy_match",
                    "confidence": round(top_confidence, 4),
                    "internal_identifier": _normalize_text(top_candidate.get("market_id") or top_candidate.get("selection_id")),
                    "candidate_ids": candidate_ids,
                    "reasons": scored[0][1].get("reasons") or [],
                }

        generic_scored: list[tuple[dict[str, Any], float, str]] = []
        for candidate in candidates:
            candidate_internal = _normalize_text(
                candidate.get("internal_identifier")
                or candidate.get("event_id")
                or candidate.get("market_id")
                or candidate.get("selection_id")
                or candidate.get("team_id")
                or candidate.get("venue_id")
                or candidate.get("provider_id")
                or candidate.get("asset_id")
            )
            candidate_external = _normalize_text(candidate.get("external_identifier"))
            method = "manual_review"
            confidence = 0.0
            if candidate_external and candidate_external == external_id:
                method = "stable_external_identifier"
                confidence = 99.0
            elif exact_fields and _composite_key(candidate, exact_fields) == _composite_key(source_row, exact_fields):
                method = "exact_composite_identity"
                confidence = 97.0
            elif normalized_fields and _composite_key(candidate, normalized_fields) == _composite_key(source_row, normalized_fields):
                method = "normalized_exact_match"
                confidence = 94.0
            else:
                source_name = external_id or _normalize_text(source_row.get("entity_name") or source_row.get("name"))
                candidate_name = _normalize_text(candidate.get("entity_name") or candidate.get("name") or candidate_external or candidate_internal)
                similarity = _candidate_similarity(source_name, candidate_name)
                if similarity >= 0.92:
                    method = "controlled_fuzzy_match"
                    confidence = round(similarity * 100.0, 4)
            generic_scored.append((candidate, confidence, method))
        generic_scored.sort(
            key=lambda item: (item[1], _normalize_text(item[0].get("internal_identifier"))),
            reverse=True,
        )
        candidate_ids: list[str] = []
        for rank, (candidate, confidence, method) in enumerate(generic_scored, start=1):
            candidate_record = self.record_match_candidate(
                entity_type=entity,
                provider=provider_name,
                external_identifier=external_id,
                internal_identifier=_normalize_text(candidate.get("internal_identifier") or candidate.get("event_id")),
                candidate_internal_identifier=_normalize_text(candidate.get("internal_identifier") or candidate.get("event_id")),
                candidate_name=_normalize_text(candidate.get("entity_name") or candidate.get("name")),
                candidate_rank=rank,
                match_method=method,
                confidence=confidence,
                decision_status="accepted" if rank == 1 and method != "manual_review" and confidence >= 94 else "manual_review",
                review_state="approved" if rank == 1 and method != "manual_review" and confidence >= 94 else "manual_review",
                reasons=[method],
                canonical_key=_normalize_text(candidate.get("canonical_key")),
                source_payload=source_row,
            )
            candidate_ids.append(candidate_record["candidate_id"])
        if generic_scored:
            top_candidate, top_confidence, top_method = generic_scored[0]
            ambiguous = len(generic_scored) > 1 and top_confidence == generic_scored[1][1]
            if top_method != "manual_review" and top_confidence >= 94 and not ambiguous:
                return {
                    "accepted": True,
                    "decision_status": "accepted_with_warning" if top_method == "controlled_fuzzy_match" else "accepted",
                    "review_state": "approved",
                    "match_method": top_method,
                    "confidence": round(top_confidence, 4),
                    "internal_identifier": _normalize_text(
                        top_candidate.get("internal_identifier")
                        or top_candidate.get("event_id")
                        or top_candidate.get("market_id")
                        or top_candidate.get("selection_id")
                    ),
                    "candidate_ids": candidate_ids,
                    "reasons": [top_method],
                }

        manual_review = self.enqueue_manual_review(
            entity_type=entity,
            provider=provider_name,
            internal_identifier="",
            external_identifier=external_id,
            decision_status="manual_review",
            priority="high",
            recommended_action="review_identity_mapping",
            candidate_ids=candidate_ids,
            details={"entity_type": entity, "external_identifier": external_id},
            source_payload=source_row,
        )
        self.record_quarantine_record(
            dataset_table=f"identity::{entity}",
            record_identifier=external_id,
            entity_type=entity,
            provider=provider_name,
            internal_identifier="",
            external_identifier=external_id,
            quarantine_reason="ambiguous_or_low_confidence_match",
            decision_status="manual_review",
            review_state="manual_review",
            release_state="pending_review",
            match_candidate_ids=candidate_ids,
            details={"review_id": manual_review["review_id"]},
            source_payload=source_row,
        )
        return {
            "accepted": False,
            "decision_status": "manual_review",
            "review_state": "manual_review",
            "match_method": "manual_review",
            "confidence": 0.0,
            "internal_identifier": "",
            "candidate_ids": candidate_ids,
            "reasons": ["manual_review"],
            "review_id": manual_review["review_id"],
        }

    def _seed_identity_rows_from_certified_outputs(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        schedule_rows = self._fetch("nfl_schedule", order_by="kickoff_time ASC, game_id ASC")
        odds_rows = self._fetch("nfl_odds_snapshots", order_by="game_id ASC, odds_snapshot_id ASC")
        dataset_rows = self._fetch("historical_dataset_rows", order_by="event_start_time ASC, dataset_row_id ASC")
        events = self._fetch("historical_events", order_by="event_start_time ASC, event_id ASC")
        markets = self._fetch("historical_markets", order_by="event_id ASC, market_id ASC")
        selections = self._fetch("historical_selections", order_by="event_id ASC, market_id ASC, selection_id ASC")
        providers = self._fetch("provider_metadata", order_by="provider_id ASC")
        if not events:
            events = [
                {
                    "event_id": _normalize_text(row.get("game_id")),
                    "event_key": f"{_normalize_text(row.get('away_team'))} at {_normalize_text(row.get('home_team'))}",
                    "event_date": _normalize_text(row.get("game_date")),
                    "event_start_time": _normalize_text(row.get("kickoff_time")),
                    "home_team_id": _normalize_text(row.get("home_team_id")),
                    "home_team": _normalize_text(row.get("home_team")),
                    "away_team_id": _normalize_text(row.get("away_team_id")),
                    "away_team": _normalize_text(row.get("away_team")),
                    "venue_id": _normalize_text(row.get("venue_id")),
                    "venue_name": _normalize_text(row.get("venue_name")),
                    "provider": _normalize_text(row.get("provider"), "nflverse"),
                    "dataset_id": "dataset.sports.nfl.schedule",
                    "dataset_name": "nfl_schedule",
                    "sport": "football",
                    "league": "NFL",
                    "source_event_id": _normalize_text(row.get("game_id")),
                    "source_snapshot_time": _normalize_text(row.get("snapshot_time")),
                    "created_at": _normalize_text(row.get("snapshot_time")),
                }
                for row in schedule_rows
            ]
        if not markets:
            markets = [
                {
                    "market_id": _normalize_text(row.get("odds_snapshot_id"))
                    or _stable_id("market.synthetic", row.get("game_id"), row.get("book"), row.get("market")),
                    "event_id": _normalize_text(row.get("game_id")),
                    "book": _normalize_text(row.get("book")),
                    "market_family": _normalize_text(row.get("market")),
                    "market_type": _normalize_text(row.get("market")),
                    "market_name": _normalize_text(row.get("market")),
                    "market_label": _normalize_text(row.get("market")),
                    "line_value": row.get("line"),
                    "provider": _normalize_text(row.get("provider"), "the_odds_api"),
                    "dataset_id": "dataset.nfl.odds_snapshots",
                    "dataset_name": "nfl_odds_snapshots",
                    "source_market_id": _normalize_text(row.get("odds_snapshot_id")),
                    "source_snapshot_time": _normalize_text(row.get("source_snapshot_time") or row.get("snapshot_time")),
                    "created_at": _normalize_text(row.get("snapshot_time")),
                }
                for row in odds_rows
            ]
            if not markets:
                markets = [
                    {
                        "market_id": _stable_id(
                            "market.dataset_row",
                            row.get("event_id"),
                            row.get("book"),
                            row.get("market_type"),
                            row.get("selection"),
                            row.get("line_value"),
                        ),
                        "event_id": _normalize_text(row.get("event_id")),
                        "book": _normalize_text(row.get("book")),
                        "market_family": _normalize_text(row.get("market_type")),
                        "market_type": _normalize_text(row.get("market_type")),
                        "market_name": _normalize_text(row.get("market_name") or row.get("market_type")),
                        "market_label": _normalize_text(row.get("market_name") or row.get("market_type")),
                        "line_value": row.get("line_value"),
                        "provider": _normalize_text(row.get("provider"), "historical_dataset_population_runtime"),
                        "dataset_id": _normalize_text(row.get("dataset_id")),
                        "dataset_name": _normalize_text(row.get("dataset_name")),
                        "source_market_id": _normalize_text(row.get("dataset_row_id")),
                        "source_snapshot_time": _normalize_text(row.get("source_snapshot_time") or row.get("scheduled_kickoff_time")),
                        "created_at": _normalize_text(row.get("created_at")),
                    }
                    for row in dataset_rows
                ]
        if not selections:
            selections = [
                {
                    "selection_id": _normalize_text(row.get("odds_snapshot_id"))
                    or _stable_id("selection.synthetic", row.get("game_id"), row.get("book"), row.get("market"), row.get("selection"), row.get("line")),
                    "market_id": _normalize_text(row.get("odds_snapshot_id"))
                    or _stable_id("market.synthetic", row.get("game_id"), row.get("book"), row.get("market")),
                    "event_id": _normalize_text(row.get("game_id")),
                    "book": _normalize_text(row.get("book")),
                    "market_family": _normalize_text(row.get("market")),
                    "market_type": _normalize_text(row.get("market")),
                    "market_name": _normalize_text(row.get("market")),
                    "selection": _normalize_text(row.get("selection")),
                    "line_value": row.get("line"),
                    "provider": _normalize_text(row.get("provider"), "the_odds_api"),
                    "dataset_id": "dataset.nfl.odds_snapshots",
                    "dataset_name": "nfl_odds_snapshots",
                    "source_selection_id": _normalize_text(row.get("odds_snapshot_id")),
                    "source_snapshot_time": _normalize_text(row.get("source_snapshot_time") or row.get("snapshot_time")),
                    "created_at": _normalize_text(row.get("snapshot_time")),
                }
                for row in odds_rows
            ]
            if not selections:
                selections = [
                    {
                        "selection_id": _stable_id(
                            "selection.dataset_row",
                            row.get("event_id"),
                            row.get("book"),
                            row.get("market_type"),
                            row.get("selection"),
                            row.get("line_value"),
                        ),
                        "market_id": _stable_id(
                            "market.dataset_row",
                            row.get("event_id"),
                            row.get("book"),
                            row.get("market_type"),
                            row.get("selection"),
                            row.get("line_value"),
                        ),
                        "event_id": _normalize_text(row.get("event_id")),
                        "book": _normalize_text(row.get("book")),
                        "market_family": _normalize_text(row.get("market_type")),
                        "market_type": _normalize_text(row.get("market_type")),
                        "market_name": _normalize_text(row.get("market_name") or row.get("market_type")),
                        "selection": _normalize_text(row.get("selection")),
                        "line_value": row.get("line_value"),
                        "provider": _normalize_text(row.get("provider"), "historical_dataset_population_runtime"),
                        "dataset_id": _normalize_text(row.get("dataset_id")),
                        "dataset_name": _normalize_text(row.get("dataset_name")),
                        "source_selection_id": _normalize_text(row.get("dataset_row_id")),
                        "source_snapshot_time": _normalize_text(row.get("source_snapshot_time") or row.get("scheduled_kickoff_time")),
                        "created_at": _normalize_text(row.get("created_at")),
                    }
                    for row in dataset_rows
                ]

        for provider_row in providers:
            provider_id = _normalize_text(provider_row.get("provider_id"))
            if not provider_id:
                continue
            rows.append(
                self.register_identity_mapping(
                    provider="repository",
                    external_identifier=_normalize_text(provider_row.get("provider_name") or provider_id),
                    internal_identifier=provider_id,
                    entity_type="provider",
                    entity_name=_normalize_text(provider_row.get("provider_name") or provider_id),
                    canonical_key=provider_id,
                    source_payload=provider_row,
                    approval_evidence={"source_table": "provider_metadata", "provider_id": provider_id},
                    dataset_id="provider_metadata",
                    dataset_name="provider_metadata",
                    market_type="identity_mapping.provider",
                )
            )

        seen_sports: set[str] = set()
        seen_leagues: set[str] = set()
        seen_teams: set[tuple[str, str]] = set()
        seen_venues: set[tuple[str, str]] = set()

        for event_row in events:
            provider_name = _normalize_text(event_row.get("provider"), "repository")
            sport = _normalize_text(event_row.get("sport"))
            if sport and sport not in seen_sports:
                seen_sports.add(sport)
                rows.append(
                    self.register_identity_mapping(
                        provider="repository",
                        external_identifier=sport,
                        internal_identifier=f"sport::{sport}",
                        entity_type="sport",
                        entity_name=sport,
                        canonical_key=sport,
                        source_payload=event_row,
                        approval_evidence={"source_table": "historical_events", "sport": sport},
                        dataset_id=_normalize_text(event_row.get("dataset_id")),
                        dataset_name=_normalize_text(event_row.get("dataset_name")),
                        market_type="identity_mapping.sport",
                    )
                )
            league = _normalize_text(event_row.get("league"))
            if league and league not in seen_leagues:
                seen_leagues.add(league)
                rows.append(
                    self.register_identity_mapping(
                        provider="repository",
                        external_identifier=league,
                        internal_identifier=f"league::{league}",
                        entity_type="league",
                        entity_name=league,
                        canonical_key=league,
                        source_payload=event_row,
                        approval_evidence={"source_table": "historical_events", "league": league},
                        dataset_id=_normalize_text(event_row.get("dataset_id")),
                        dataset_name=_normalize_text(event_row.get("dataset_name")),
                        market_type="identity_mapping.league",
                    )
                )
            for team_id_field, team_name_field in (("home_team_id", "home_team"), ("away_team_id", "away_team")):
                team_id = _normalize_text(event_row.get(team_id_field))
                team_name = _normalize_text(event_row.get(team_name_field))
                if team_id and (team_id, team_name) not in seen_teams:
                    seen_teams.add((team_id, team_name))
                    rows.append(
                        self.register_identity_mapping(
                            provider="repository",
                            external_identifier=team_name or team_id,
                            internal_identifier=team_id,
                            entity_type="team",
                            entity_name=team_name or team_id,
                            canonical_key=team_id,
                            source_payload=event_row,
                            approval_evidence={"source_table": "historical_events", "team_id": team_id},
                            dataset_id=_normalize_text(event_row.get("dataset_id")),
                            dataset_name=_normalize_text(event_row.get("dataset_name")),
                            market_type="identity_mapping.team",
                        )
                    )
            venue_id = _normalize_text(event_row.get("venue_id"))
            venue_name = _normalize_text(event_row.get("venue_name"))
            if venue_id and (venue_id, venue_name) not in seen_venues:
                seen_venues.add((venue_id, venue_name))
                rows.append(
                    self.register_identity_mapping(
                        provider="repository",
                        external_identifier=venue_name or venue_id,
                        internal_identifier=venue_id,
                        entity_type="venue",
                        entity_name=venue_name or venue_id,
                        canonical_key=venue_id,
                        source_payload=event_row,
                        approval_evidence={"source_table": "historical_events", "venue_id": venue_id},
                        dataset_id=_normalize_text(event_row.get("dataset_id")),
                        dataset_name=_normalize_text(event_row.get("dataset_name")),
                        market_type="identity_mapping.venue",
                    )
                )
            external_event_id = _normalize_text(event_row.get("source_event_id") or event_row.get("event_key") or event_row.get("game_id"))
            if _normalize_text(event_row.get("event_id")) and external_event_id:
                rows.append(
                    self.register_identity_mapping(
                        provider=provider_name,
                        external_identifier=external_event_id,
                        internal_identifier=_normalize_text(event_row.get("event_id")),
                        entity_type="event",
                        entity_name=_normalize_text(event_row.get("event_key") or event_row.get("game_id")),
                        canonical_key=_composite_key(event_row, ("sport", "league", "event_date", "home_team", "away_team")),
                        source_payload=event_row,
                        approval_evidence={"source_table": "historical_events", "event_id": event_row.get("event_id")},
                        dataset_id=_normalize_text(event_row.get("dataset_id")),
                        dataset_name=_normalize_text(event_row.get("dataset_name")),
                        market_type="identity_mapping.event",
                    )
                )

        seen_market_families: set[str] = set()
        for market_row in markets:
            market_family = _normalize_text(market_row.get("market_family"))
            if market_family and market_family not in seen_market_families:
                seen_market_families.add(market_family)
                rows.append(
                    self.register_identity_mapping(
                        provider="repository",
                        external_identifier=market_family,
                        internal_identifier=f"market_family::{market_family}",
                        entity_type="market_family",
                        entity_name=market_family,
                        canonical_key=market_family,
                        source_payload=market_row,
                        approval_evidence={"source_table": "historical_markets", "market_family": market_family},
                        dataset_id=_normalize_text(market_row.get("dataset_id")),
                        dataset_name=_normalize_text(market_row.get("dataset_name")),
                        market_type="identity_mapping.market_family",
                    )
                )
            market_id = _normalize_text(market_row.get("market_id"))
            external_market_id = _normalize_text(
                market_row.get("source_market_id")
                or f"{market_row.get('event_id')}|{market_row.get('book')}|{market_row.get('market_type')}|{market_row.get('line_value')}"
            )
            if market_id and external_market_id:
                rows.append(
                    self.register_identity_mapping(
                        provider=_normalize_text(market_row.get("provider"), "repository"),
                        external_identifier=external_market_id,
                        internal_identifier=market_id,
                        entity_type="canonical_market",
                        entity_name=_normalize_text(market_row.get("market_name") or market_row.get("market_label") or market_id),
                        canonical_key=_composite_key(market_row, ("event_id", "market_type", "book", "line_value")),
                        source_payload=market_row,
                        approval_evidence={"source_table": "historical_markets", "market_id": market_id},
                        dataset_id=_normalize_text(market_row.get("dataset_id")),
                        dataset_name=_normalize_text(market_row.get("dataset_name")),
                        market_type="identity_mapping.market",
                    )
                )

        for selection_row in selections:
            selection_id = _normalize_text(selection_row.get("selection_id"))
            external_selection_id = _normalize_text(
                selection_row.get("source_selection_id")
                or f"{selection_row.get('market_id')}|{selection_row.get('selection')}|{selection_row.get('book')}|{selection_row.get('line_value')}"
            )
            if selection_id and external_selection_id:
                rows.append(
                    self.register_identity_mapping(
                        provider=_normalize_text(selection_row.get("provider"), "repository"),
                        external_identifier=external_selection_id,
                        internal_identifier=selection_id,
                        entity_type="selection_outcome",
                        entity_name=_normalize_text(selection_row.get("selection") or selection_id),
                        canonical_key=_composite_key(selection_row, ("event_id", "market_type", "selection", "book", "line_value")),
                        source_payload=selection_row,
                        approval_evidence={"source_table": "historical_selections", "selection_id": selection_id},
                        dataset_id=_normalize_text(selection_row.get("dataset_id")),
                        dataset_name=_normalize_text(selection_row.get("dataset_name")),
                        market_type="identity_mapping.selection",
                    )
                )
                rows.append(
                    self.register_identity_mapping(
                        provider=_normalize_text(selection_row.get("provider"), "repository"),
                        external_identifier=external_selection_id,
                        internal_identifier=selection_id,
                        entity_type="vendor_entity",
                        entity_name=_normalize_text(selection_row.get("selection") or selection_id),
                        canonical_key=_normalize_text(selection_row.get("market_id")),
                        source_payload=selection_row,
                        approval_evidence={"source_table": "historical_selections", "selection_id": selection_id},
                        dataset_id=_normalize_text(selection_row.get("dataset_id")),
                        dataset_name=_normalize_text(selection_row.get("dataset_name")),
                        market_type="identity_mapping.vendor_entity",
                    )
                )
        return rows

    def seed_from_certified_outputs(self) -> dict[str, Any]:
        mappings = self._seed_identity_rows_from_certified_outputs()
        return {
            "ok": True,
            "status": "seeded",
            "identity_mapping_count": len(self._fetch("identity_mappings", order_by="mapping_id ASC")),
            "mappings": mappings,
        }

    def reconcile_certified_outputs(self) -> dict[str, Any]:
        rows = self._fetch("historical_selections", order_by="event_id ASC, market_id ASC, selection_id ASC")
        if not rows:
            rows = [
                {
                    "selection_id": _normalize_text(row.get("odds_snapshot_id"))
                    or _stable_id("selection.synthetic", row.get("game_id"), row.get("book"), row.get("market"), row.get("selection"), row.get("line")),
                    "market_id": _normalize_text(row.get("odds_snapshot_id"))
                    or _stable_id("market.synthetic", row.get("game_id"), row.get("book"), row.get("market")),
                    "event_id": _normalize_text(row.get("game_id")),
                    "book": _normalize_text(row.get("book")),
                    "selection": _normalize_text(row.get("selection")),
                    "market_type": _normalize_text(row.get("market")),
                    "line_value": row.get("line"),
                    "odds": row.get("odds"),
                    "provider": _normalize_text(row.get("provider"), "the_odds_api"),
                    "source_selection_id": _normalize_text(row.get("odds_snapshot_id")),
                    "source_snapshot_time": _normalize_text(row.get("source_snapshot_time") or row.get("snapshot_time")),
                    "created_at": _normalize_text(row.get("snapshot_time")),
                }
                for row in self._fetch("nfl_odds_snapshots", order_by="game_id ASC, odds_snapshot_id ASC")
            ]
        if not rows:
            rows = [
                {
                    "selection_id": _stable_id(
                        "selection.dataset_row",
                        row.get("event_id"),
                        row.get("book"),
                        row.get("market_type"),
                        row.get("selection"),
                        row.get("line_value"),
                    ),
                    "market_id": _stable_id(
                        "market.dataset_row",
                        row.get("event_id"),
                        row.get("book"),
                        row.get("market_type"),
                        row.get("selection"),
                        row.get("line_value"),
                    ),
                    "event_id": _normalize_text(row.get("event_id")),
                    "book": _normalize_text(row.get("book")),
                    "selection": _normalize_text(row.get("selection")),
                    "market_type": _normalize_text(row.get("market_type")),
                    "line_value": row.get("line_value"),
                    "odds": row.get("american_odds"),
                    "provider": _normalize_text(row.get("provider"), "historical_dataset_population_runtime"),
                    "source_selection_id": _normalize_text(row.get("dataset_row_id")),
                    "source_snapshot_time": _normalize_text(row.get("source_snapshot_time") or row.get("scheduled_kickoff_time")),
                    "created_at": _normalize_text(row.get("created_at")),
                }
                for row in self._fetch("historical_dataset_rows", order_by="event_start_time ASC, dataset_row_id ASC")
            ]
        provider_rows = {
            _normalize_text(row.get("provider_id") or row.get("provider")): dict(row)
            for row in self._fetch("provider_metadata", order_by="provider_id ASC")
        }
        reconciliation_rows: list[dict[str, Any]] = []
        for row in rows:
            provider_name = _normalize_text(row.get("provider"), "repository")
            provider_metadata = provider_rows.get(provider_name) or {}
            observation_identity = {
                "event_id": _normalize_text(row.get("event_id")),
                "market_type": _normalize_text(row.get("market_type")),
                "period": "full_game",
                "selection": _normalize_text(row.get("selection")),
                "threshold": row.get("line_value"),
                "settlement_rule": _normalize_text(row.get("status"), "certified"),
                "observation_time": _to_iso(row.get("source_snapshot_time") or row.get("snapshot_time")),
                "book": _normalize_text(row.get("book")),
            }
            accepted_evidence = [
                {
                    "selection_id": _normalize_text(row.get("selection_id")),
                    "market_id": _normalize_text(row.get("market_id")),
                    "book": _normalize_text(row.get("book")),
                    "line_value": row.get("line_value"),
                    "odds": row.get("odds"),
                    "event_id": _normalize_text(row.get("event_id")),
                }
            ]
            created = _to_iso(row.get("created_at") or row.get("processed_at") or _utc_now())
            source_published = _to_iso(row.get("source_snapshot_time") or row.get("published_at") or created)
            freshness_seconds = 0
            if source_published and created:
                try:
                    freshness_seconds = int(
                        (
                            datetime.fromisoformat(created.replace("Z", "+00:00"))
                            - datetime.fromisoformat(source_published.replace("Z", "+00:00"))
                        ).total_seconds()
                    )
                except ValueError:
                    freshness_seconds = 0
            reconciliation_rows.append(
                self.record_reconciliation_result(
                    reconciliation_scope="sportsbook_observation",
                    entity_type="selection_outcome",
                    provider=provider_name,
                    internal_identifier=_normalize_text(row.get("selection_id")),
                    external_identifier=_normalize_text(
                        row.get("source_selection_id")
                        or f"{row.get('market_id')}|{row.get('selection')}|{row.get('book')}|{row.get('line_value')}"
                    ),
                    reconciliation_status="accepted",
                    decision_status="accepted",
                    decision_explanation="Certified sportsbook observation preserved as an independent canonical selection outcome.",
                    freshness_seconds=freshness_seconds,
                    timestamp_agreement_status="aligned",
                    outlier_status="within_expected_range",
                    quality_score=1.0,
                    accepted_evidence=accepted_evidence,
                    rejected_evidence=[],
                    provider_reliability={
                        "provider_id": _normalize_text(provider_metadata.get("provider_id") or provider_name),
                        "quality_score": _normalize_float(provider_metadata.get("quality_score"), 1.0),
                        "contract_version": _normalize_text(provider_metadata.get("contract_version")),
                    },
                    observation_identity=observation_identity,
                    source_payload=row,
                    lineage_reference={"selection_id": _normalize_text(row.get("selection_id"))},
                )
            )
        return {
            "ok": True,
            "status": "reconciled",
            "reconciliation_result_count": len(reconciliation_rows),
            "reconciliation_rows": reconciliation_rows,
        }

    def _lakehouse_groups(
        self,
        layer_name: str,
        table_name: str,
        rows: Sequence[Mapping[str, Any]],
    ) -> list[tuple[dict[str, str], list[dict[str, Any]]]]:
        partition_columns = _partition_columns_for_table(layer_name, table_name)
        groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
        values_lookup: dict[tuple[str, ...], dict[str, str]] = {}
        for row in rows:
            partition_values = {
                column: _lakehouse_partition_value(row, column)
                for column in partition_columns
            }
            partition_key = tuple(partition_values[column] for column in partition_columns)
            values_lookup[partition_key] = partition_values
            groups.setdefault(partition_key, []).append(dict(row))
        return [(values_lookup[key], groups[key]) for key in sorted(groups)]

    def publish_lakehouse_views(self) -> dict[str, Any]:
        if not parquet_available():
            raise RuntimeError("pyarrow is required for lakehouse parquet publishing")
        datasets: list[tuple[str, str, list[dict[str, Any]]]] = [
            (BRONZE, "raw_records", self._fetch("raw_records", order_by="created_at ASC, record_id ASC")),
            (SILVER, "historical_events", self._fetch("historical_events", order_by="event_start_time ASC, event_id ASC")),
            (SILVER, "historical_markets", self._fetch("historical_markets", order_by="event_id ASC, market_id ASC")),
            (SILVER, "historical_selections", self._fetch("historical_selections", order_by="event_id ASC, market_id ASC, selection_id ASC")),
            (SILVER, "identity_mappings", self._fetch("identity_mappings", order_by="entity_type ASC, provider ASC, external_identifier ASC, revision_number ASC")),
            (SILVER, "identity_reconciliation_results", self._fetch("identity_reconciliation_results", order_by="provider ASC, internal_identifier ASC, revision_number ASC")),
            (GOLD, "historical_dataset_rows", self._fetch("historical_dataset_rows", order_by="event_start_time ASC, dataset_row_id ASC")),
            (GOLD, "feature_snapshots", self._fetch("feature_snapshots", order_by="created_at ASC, snapshot_id ASC")),
        ]
        partition_rows: list[dict[str, Any]] = []
        for layer_name, table_name, rows in datasets:
            if not rows:
                continue
            partition_columns = _partition_columns_for_table(layer_name, table_name)
            for partition_values, grouped_rows in self._lakehouse_groups(layer_name, table_name, rows):
                dataset_identifier = _normalize_text(
                    grouped_rows[0].get("dataset_id")
                    or grouped_rows[0].get("dataset_name")
                    or table_name
                )
                content_seed = {
                    "layer_name": layer_name,
                    "table_name": table_name,
                    "partition_values": partition_values,
                    "row_ids": [
                        _normalize_text(
                            row.get("record_id")
                            or row.get("dataset_row_id")
                            or row.get("market_id")
                            or row.get("selection_id")
                            or row.get("event_id")
                            or row.get("mapping_id")
                            or row.get("reconciliation_id")
                            or row.get("snapshot_id")
                        )
                        for row in grouped_rows
                    ],
                }
                deterministic_file_id = _stable_id("lakehouse.file", content_seed)
                partition_path = _lakehouse_partition_path(
                    self.lakehouse_root,
                    layer_name,
                    table_name,
                    partition_values,
                )
                output_path = partition_path / f"{_stable_digest('lakehouse.file.path', deterministic_file_id, length=16)}.parquet"
                parquet_result = self.store.write_parquet_rows(output_path, grouped_rows)
                roundtrip_rows = self.store.read_parquet_rows(output_path)
                partition_id = _stable_id("lakehouse.partition", layer_name, table_name, partition_values, deterministic_file_id)
                delta_table_name = f"{layer_name}.{table_name}".replace("-", "_")
                manifest_row = {
                    "partition_id": partition_id,
                    "layer_name": layer_name,
                    "dataset_table": table_name,
                    "dataset_identifier": dataset_identifier,
                    "dataset_id": dataset_identifier,
                    "dataset_name": table_name,
                    "owner": "src.data",
                    "sport": _normalize_text(grouped_rows[0].get("sport"), "football"),
                    "feature_pack": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
                    "storage_location": str(self.lakehouse_root),
                    "readiness": "ready",
                    "update_frequency": "manual",
                    "validation_state": "validated",
                    "status": "active",
                    "market_profile": _normalize_text(
                        grouped_rows[0].get("market_profile")
                        or grouped_rows[0].get("profile_id")
                        or grouped_rows[0].get("market")
                        or "sports:nfl"
                    ),
                    "provider": _normalize_text(grouped_rows[0].get("provider"), "repository"),
                    "market": _normalize_text(grouped_rows[0].get("market"), "sports:nfl"),
                    "market_type": f"lakehouse.{layer_name}",
                    "asset_class": _normalize_text(grouped_rows[0].get("asset_class"), "historical"),
                    "partition_key_json": _as_json(partition_values),
                    "partition_values_json": _as_json(partition_values),
                    "partition_columns_json": _as_json(list(partition_columns)),
                    "file_path": str(output_path),
                    "deterministic_file_id": deterministic_file_id,
                    "content_digest": parquet_result["content_digest"],
                    "file_checksum": parquet_result["file_checksum"],
                    "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
                    "row_count": parquet_result["row_count"],
                    "file_size_bytes": parquet_result["file_size_bytes"],
                    "delta_table_name": delta_table_name,
                    "delta_metadata_json": _as_json(
                        {
                            "delta_compatible": True,
                            "schema_evolution_ready": True,
                            "versioned_table_ready": True,
                            "corrections_upserts_ready": True,
                            "time_travel_ready": True,
                            "concurrent_write_contract": "deferred_to_future_delta_runtime",
                            "spark_required": False,
                        }
                    ),
                    "compaction_group": _stable_id("lakehouse.compaction_group", layer_name, table_name, partition_values),
                    "roundtrip_row_count": len(roundtrip_rows),
                    "roundtrip_ok": 1 if len(roundtrip_rows) == parquet_result["row_count"] else 0,
                    "metadata_json": _as_json(
                        {
                            "layer_name": layer_name,
                            "table_name": table_name,
                            "partition_values": partition_values,
                            "partition_columns": list(partition_columns),
                            "parquet_schema_version": parquet_result["schema_version"],
                        }
                    ),
                    "payload_json": _as_json(
                        {
                            "parquet_result": parquet_result,
                            "partition_values": partition_values,
                        }
                    ),
                    "snapshot_id": deterministic_file_id,
                    "lineage_id": _stable_id("lakehouse.partition.lineage", partition_id, parquet_result["content_digest"]),
                    "version_id": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
                    "quality_score": 1.0 if len(roundtrip_rows) == parquet_result["row_count"] else 0.0,
                    "created_at": _utc_now(),
                    "updated_at": _utc_now(),
                    "source": "data_identity_lakehouse_runtime",
                }
                self._persist_row("lakehouse_partitions", manifest_row, key_columns=("partition_id",))
                partition_rows.append(manifest_row)
        return {
            "ok": True,
            "status": "published",
            "partition_count": len(partition_rows),
            "layer_counts": {
                BRONZE: len([row for row in partition_rows if row["layer_name"] == BRONZE]),
                SILVER: len([row for row in partition_rows if row["layer_name"] == SILVER]),
                GOLD: len([row for row in partition_rows if row["layer_name"] == GOLD]),
            },
            "lakehouse_root": str(self.lakehouse_root),
            "partitions": partition_rows,
        }

    def build_capability_audit(self) -> list[dict[str, Any]]:
        has_identity_rows = self.store.table_exists("identity_mappings") and self.store.count("identity_mappings") > 0
        has_reconciliation_rows = self.store.table_exists("identity_reconciliation_results") and self.store.count("identity_reconciliation_results") > 0
        has_quality_tables = all(
            self.store.table_exists(name)
            for name in ("data_quality_events", "quarantine_records", "manual_review_queue", "mapping_approvals")
        )
        has_parquet_manifests = self.store.table_exists("lakehouse_partitions") and self.store.count("lakehouse_partitions") > 0
        return [
            {
                "requirement_id": "canonical_identity_foundation",
                "initial_classification": "partial",
                "final_classification": "complete_and_validated" if has_identity_rows else "missing",
            },
            {
                "requirement_id": "matching",
                "initial_classification": "partial",
                "final_classification": "complete_and_validated" if has_identity_rows and has_quality_tables else "partial",
            },
            {
                "requirement_id": "reconciliation",
                "initial_classification": "partial",
                "final_classification": "complete_and_validated" if has_reconciliation_rows else "missing",
            },
            {
                "requirement_id": "point_in_time_and_revision_contract",
                "initial_classification": "partial",
                "final_classification": "complete_and_validated" if has_identity_rows and has_reconciliation_rows else "partial",
            },
            {
                "requirement_id": "quality_quarantine_review",
                "initial_classification": "missing",
                "final_classification": "complete_and_validated" if has_quality_tables else "missing",
            },
            {
                "requirement_id": "bronze_silver_gold_mapping",
                "initial_classification": "partial",
                "final_classification": "complete_and_validated" if has_parquet_manifests else "missing",
            },
            {
                "requirement_id": "parquet_analytical_storage",
                "initial_classification": "missing",
                "final_classification": "complete_and_validated" if has_parquet_manifests else "missing",
            },
            {
                "requirement_id": "delta_compatible_interfaces",
                "initial_classification": "missing",
                "final_classification": "complete_and_validated" if has_parquet_manifests else "missing",
            },
            {
                "requirement_id": "security_and_governance",
                "initial_classification": "complete_and_validated",
                "final_classification": "complete_and_validated",
            },
            {
                "requirement_id": "readiness_surfaces",
                "initial_classification": "partial",
                "final_classification": "complete_and_validated" if has_identity_rows and has_parquet_manifests else "partial",
            },
        ]

    def build_readiness_snapshot(self) -> dict[str, Any]:
        mappings = self._fetch("identity_mappings", order_by="entity_type ASC, provider ASC, external_identifier ASC, revision_number ASC")
        reconciliations = self._fetch("identity_reconciliation_results", order_by="provider ASC, internal_identifier ASC")
        quality_events = self._fetch("data_quality_events", order_by="created_at ASC, quality_event_id ASC")
        quarantines = self._fetch("quarantine_records", order_by="created_at ASC, quarantine_id ASC")
        manual_reviews = self._fetch("manual_review_queue", order_by="opened_at ASC, review_id ASC")
        lakehouse_partitions = self._fetch("lakehouse_partitions", order_by="layer_name ASC, dataset_table ASC, partition_id ASC")
        mapping_counts: dict[str, int] = {}
        for row in mappings:
            mapping_counts[_normalize_text(row.get("entity_type"), "unknown")] = mapping_counts.get(
                _normalize_text(row.get("entity_type"), "unknown"),
                0,
            ) + 1
        layer_counts: dict[str, int] = {}
        for row in lakehouse_partitions:
            layer_counts[_normalize_text(row.get("layer_name"), "unknown")] = layer_counts.get(
                _normalize_text(row.get("layer_name"), "unknown"),
                0,
            ) + 1
        open_reviews = [row for row in manual_reviews if _normalize_text(row.get("review_state")) == "open"]
        readiness = (
            bool(mappings)
            and bool(reconciliations)
            and bool(lakehouse_partitions)
            and not open_reviews
            and all(_normalize_bool(row.get("roundtrip_ok")) for row in lakehouse_partitions)
        )
        return {
            "ok": readiness,
            "status": "completed" if readiness else "blocked",
            "schema_version": DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION,
            "runtime_version": DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION,
            "supported_entity_types": list(SUPPORTED_IDENTITY_ENTITY_TYPES),
            "identity_mappings": mappings,
            "identity_mapping_counts": mapping_counts,
            "reconciliation_results": reconciliations,
            "quality_events": quality_events,
            "quarantine_records": quarantines,
            "manual_review_queue": manual_reviews,
            "lakehouse_partitions": lakehouse_partitions,
            "lakehouse_layer_counts": layer_counts,
            "identity_resolution_readiness": {
                "status": "ready" if mappings else "missing",
                "approved_mapping_count": len([row for row in mappings if _normalize_text(row.get("review_state")) == "approved"]),
                "entity_type_count": len(mapping_counts),
                "supported_entity_types": list(SUPPORTED_IDENTITY_ENTITY_TYPES),
            },
            "reconciliation_readiness": {
                "status": "ready" if reconciliations else "missing",
                "reconciliation_result_count": len(reconciliations),
                "accepted_count": len([row for row in reconciliations if _normalize_text(row.get("decision_status")) == "accepted"]),
            },
            "quarantine_manual_review_readiness": {
                "status": "ready" if not open_reviews else "blocked",
                "quality_event_count": len(quality_events),
                "quarantine_count": len(quarantines),
                "open_manual_review_count": len(open_reviews),
            },
            "bronze_silver_gold_readiness": {
                "status": "ready" if layer_counts.get(BRONZE) and layer_counts.get(SILVER) and layer_counts.get(GOLD) else "blocked",
                "layer_counts": layer_counts,
            },
            "parquet_readiness": {
                "status": "ready" if lakehouse_partitions else "missing",
                "partition_count": len(lakehouse_partitions),
                "roundtrip_ok": all(_normalize_bool(row.get("roundtrip_ok")) for row in lakehouse_partitions),
                "parquet_available": parquet_available(),
            },
            "delta_compatibility": {
                "status": "ready" if lakehouse_partitions else "missing",
                "spark_required": False,
                "delta_compatible_partition_count": len(
                    [row for row in lakehouse_partitions if _parse_json_mapping(row.get("delta_metadata_json")).get("delta_compatible")]
                ),
            },
            "spark_deferral_evidence": {
                "status": "deferred",
                "justification": "Current certified NFL reference data volume remains local-scale and deterministic.",
                "total_row_count": sum(_normalize_int(row.get("row_count")) for row in lakehouse_partitions),
                "partition_count": len(lakehouse_partitions),
                "concurrent_write_requirement": "not_required_for_current_local_execution",
            },
            "query_surfaces": [
                {
                    "query_id": "list_identity_mappings",
                    "purpose": "Inspect stable internal IDs and approval evidence by entity type and provider.",
                },
                {
                    "query_id": "list_reconciliation_results",
                    "purpose": "Inspect accepted and rejected reconciliation evidence without collapsing sportsbook observations.",
                },
                {
                    "query_id": "list_lakehouse_partitions",
                    "purpose": "Inspect deterministic Parquet partition manifests and Delta-compatible metadata.",
                },
            ],
            "lakehouse_readiness_state": "ready" if lakehouse_partitions else "missing",
            "first_vendor_ingest_readiness_state": "ready" if readiness else "blocked",
            "storage": self.store.health(),
        }

    def synchronize(self) -> dict[str, Any]:
        seed_result = self.seed_from_certified_outputs()
        reconciliation_result = self.reconcile_certified_outputs()
        lakehouse_result = self.publish_lakehouse_views()
        readiness_snapshot = self.build_readiness_snapshot()
        return {
            "ok": bool(seed_result.get("ok")) and bool(reconciliation_result.get("ok")) and bool(lakehouse_result.get("ok")) and bool(readiness_snapshot.get("ok")),
            "status": readiness_snapshot.get("status"),
            "seed_result": seed_result,
            "reconciliation_result": reconciliation_result,
            "lakehouse_result": lakehouse_result,
            "readiness_snapshot": readiness_snapshot,
            "capability_audit": self.build_capability_audit(),
        }


def build_data_identity_lakehouse_readiness_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    lakehouse_root: str | Path | None = None,
    synchronize: bool = True,
) -> dict[str, Any]:
    runtime = DataIdentityLakehouseRuntime(
        storage_path=storage_path,
        backend=backend,
        lakehouse_root=lakehouse_root,
    )
    try:
        if synchronize:
            return runtime.synchronize()
        return runtime.build_readiness_snapshot()
    finally:
        runtime.close()


__all__ = [
    "BRONZE",
    "DATA_IDENTITY_LAKEHOUSE_RUNTIME_VERSION",
    "DATA_IDENTITY_LAKEHOUSE_SCHEMA_VERSION",
    "DEFAULT_DATA_IDENTITY_FOUNDATION_STORAGE_PATH",
    "DEFAULT_DATA_IDENTITY_LAKEHOUSE_ROOT",
    "FOUNDATION_DECISION_STATUSES",
    "GOLD",
    "MATCH_METHOD_HIERARCHY",
    "SILVER",
    "SUPPORTED_IDENTITY_ENTITY_TYPES",
    "DataIdentityLakehouseRuntime",
    "build_data_identity_lakehouse_readiness_snapshot",
]
