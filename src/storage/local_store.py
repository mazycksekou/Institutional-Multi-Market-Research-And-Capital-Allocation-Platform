from __future__ import annotations

import hashlib
import importlib
import json
import sqlite3
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:  # pragma: no cover - optional backend
    import duckdb as _duckdb  # type: ignore
except Exception:  # pragma: no cover - import-safe fallback
    _duckdb = None  # type: ignore

def _import_pyarrow_modules() -> tuple[Any, Any]:
    try:  # pragma: no cover - optional backend
        return importlib.import_module("pyarrow"), importlib.import_module("pyarrow.parquet")
    except Exception:
        base_site_packages = Path(sys.base_prefix) / "Lib" / "site-packages"
        if base_site_packages.exists():
            base_path = str(base_site_packages)
            if base_path not in sys.path:
                sys.path.append(base_path)
            try:  # pragma: no cover - optional backend
                return importlib.import_module("pyarrow"), importlib.import_module("pyarrow.parquet")
            except Exception:
                pass
    return None, None


_pyarrow, _pyarrow_parquet = _import_pyarrow_modules()


LOCAL_STORAGE_SCHEMA_VERSION = "src.storage.local_store.v1"
PARQUET_STORAGE_INTERFACE_VERSION = "src.storage.local_store.parquet.v1"
SUPPORTED_LOCAL_STORAGE_BACKENDS = ("sqlite", "duckdb")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def backend_available(backend: str) -> bool:
    backend_name = str(backend or "").strip().lower()
    if backend_name == "sqlite":
        return True
    if backend_name == "duckdb":
        return _duckdb is not None
    return False


def parquet_available() -> bool:
    return _pyarrow is not None and _pyarrow_parquet is not None


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Unsupported value for JSON encoding: {type(value)!r}")


def _normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        value = asdict(value)
    elif hasattr(value, "as_dict"):
        value = value.as_dict()
    if isinstance(value, (Mapping, list, tuple, set)):
        return json.dumps(value, default=_json_default, sort_keys=True, ensure_ascii=False)
    return str(value)


def _normalize_parquet_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        value = asdict(value)
    elif hasattr(value, "as_dict"):
        value = value.as_dict()
    if isinstance(value, set):
        value = sorted(value)
    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, Mapping):
        return json.dumps(dict(value), default=_json_default, sort_keys=True, ensure_ascii=False)
    if isinstance(value, list):
        return json.dumps(list(value), default=_json_default, sort_keys=True, ensure_ascii=False)
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _canonicalize_parquet_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str], str]:
    columns = sorted({str(key) for row in rows for key in dict(row)})
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        payload = {column: _normalize_parquet_value(dict(row).get(column)) for column in columns}
        normalized_rows.append(payload)
    normalized_rows.sort(
        key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False, default=str)
    )
    content_digest = hashlib.sha256(
        json.dumps(normalized_rows, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()
    return normalized_rows, columns, content_digest


def _quote_identifier(name: str) -> str:
    clean = str(name).replace('"', '""')
    return f'"{clean}"'


def _common_columns() -> list[tuple[str, str]]:
    return [
        ("schema_version", "TEXT"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
        ("source", "TEXT"),
        ("provider", "TEXT"),
        ("market", "TEXT"),
        ("market_type", "TEXT"),
        ("asset_class", "TEXT"),
        ("snapshot_id", "TEXT"),
        ("lineage_id", "TEXT"),
        ("version_id", "TEXT"),
        ("quality_score", "REAL"),
    ]


def _math_engine_columns(*columns: tuple[str, str]) -> list[tuple[str, str]]:
    return [
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("math_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        *_common_columns(),
        ("batch_id", "TEXT"),
        ("snapshot_kind", "TEXT"),
        ("math_pack_version", "TEXT"),
        ("source_feature_dataset_id", "TEXT"),
        ("source_feature_dataset_name", "TEXT"),
        ("source_feature_batch_id", "TEXT"),
        ("source_feature_version_id", "TEXT"),
        ("source_feature_certification_id", "TEXT"),
        ("source_feature_dataset_certification_id", "TEXT"),
        ("source_feature_population_summary_id", "TEXT"),
        ("source_feature_evidence_package_id", "TEXT"),
        ("source_feature_batch_lineage_id", "TEXT"),
        ("source_feature_row_count", "INTEGER"),
        ("source_feature_snapshot_count", "INTEGER"),
        ("source_feature_definition_count", "INTEGER"),
        ("dataset_row_id", "TEXT"),
        ("decision_context_id", "TEXT"),
        ("feature_context_id", "TEXT"),
        ("event_id", "TEXT"),
        ("game_id", "TEXT"),
        ("season", "INTEGER"),
        ("week", "INTEGER"),
        ("home_team_id", "TEXT"),
        ("away_team_id", "TEXT"),
        ("team_side", "TEXT"),
        ("target_team_id", "TEXT"),
        ("opponent_team_id", "TEXT"),
        ("home_team", "TEXT"),
        ("away_team", "TEXT"),
        ("selection", "TEXT"),
        ("book", "TEXT"),
        ("scheduled_kickoff_time", "TEXT"),
        ("decision_cutoff_time", "TEXT"),
        ("cutoff_policy_version", "TEXT"),
        ("point_in_time_status", "TEXT"),
        ("predictor_outcome_separation_status", "TEXT"),
        ("decision_readiness_status", "TEXT"),
        ("engine_id", "TEXT"),
        ("engine_name", "TEXT"),
        ("engine_family", "TEXT"),
        ("engine_version", "TEXT"),
        ("classification", "TEXT"),
        ("value_type", "TEXT"),
        ("unit", "TEXT"),
        ("engine_owner", "TEXT"),
        ("entity_scope", "TEXT"),
        ("dataset_grain_compatibility", "TEXT"),
        ("transformation_version", "TEXT"),
        ("missingness_policy", "TEXT"),
        ("engine_context_id", "TEXT"),
        ("output_feature_id", "TEXT"),
        ("required_input_feature_ids_json", "TEXT"),
        ("input_feature_count", "INTEGER"),
        ("engine_value_json", "TEXT"),
        ("engine_value_text", "TEXT"),
        ("engine_value_number", "REAL"),
        ("engine_value_boolean", "INTEGER"),
        ("engine_missingness_state", "TEXT"),
        ("engine_missingness_reason", "TEXT"),
        ("engine_definition_json", "TEXT"),
        ("engine_context_json", "TEXT"),
        ("math_engine_snapshot_grain_id", "TEXT"),
        ("math_engine_registry_schema_version", "TEXT"),
        ("engine_lineage_id", "TEXT"),
        ("engine_evidence_id", "TEXT"),
        ("source_feature_ids_json", "TEXT"),
        ("source_feature_snapshot_ids_json", "TEXT"),
        ("source_feature_lineage_ids_json", "TEXT"),
        ("source_feature_certification_ids_json", "TEXT"),
        ("source_feature_dataset_certification_ids_json", "TEXT"),
        ("source_feature_alignment_certification_ids_json", "TEXT"),
        ("source_feature_missingness_json", "TEXT"),
        ("source_feature_freshness_json", "TEXT"),
        ("source_feature_value_types_json", "TEXT"),
        ("source_feature_values_json", "TEXT"),
        ("missing_required_assets_json", "TEXT"),
        ("evidence_package_id", "TEXT"),
        ("record_count", "INTEGER"),
        ("engine_count", "INTEGER"),
        ("engine_values_json", "TEXT"),
        ("summary_json", "TEXT"),
        ("payload_json", "TEXT"),
        *columns,
    ]


def _signal_columns(*columns: tuple[str, str]) -> list[tuple[str, str]]:
    return [
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("signal_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        *_common_columns(),
        ("batch_id", "TEXT"),
        ("snapshot_kind", "TEXT"),
        ("signal_pack_version", "TEXT"),
        ("source_feature_dataset_id", "TEXT"),
        ("source_feature_dataset_name", "TEXT"),
        ("source_feature_batch_id", "TEXT"),
        ("source_feature_version_id", "TEXT"),
        ("source_feature_certification_id", "TEXT"),
        ("source_feature_dataset_certification_id", "TEXT"),
        ("source_feature_population_summary_id", "TEXT"),
        ("source_feature_evidence_package_id", "TEXT"),
        ("source_feature_batch_lineage_id", "TEXT"),
        ("source_feature_row_count", "INTEGER"),
        ("source_feature_snapshot_count", "INTEGER"),
        ("source_feature_definition_count", "INTEGER"),
        ("source_math_dataset_id", "TEXT"),
        ("source_math_dataset_name", "TEXT"),
        ("source_math_batch_id", "TEXT"),
        ("source_math_version_id", "TEXT"),
        ("source_math_certification_id", "TEXT"),
        ("source_math_dataset_certification_id", "TEXT"),
        ("source_math_population_summary_id", "TEXT"),
        ("source_math_evidence_package_id", "TEXT"),
        ("source_math_batch_lineage_id", "TEXT"),
        ("source_math_row_count", "INTEGER"),
        ("source_math_snapshot_count", "INTEGER"),
        ("source_math_definition_count", "INTEGER"),
        ("dataset_row_id", "TEXT"),
        ("decision_context_id", "TEXT"),
        ("feature_context_id", "TEXT"),
        ("event_id", "TEXT"),
        ("game_id", "TEXT"),
        ("season", "INTEGER"),
        ("week", "INTEGER"),
        ("home_team_id", "TEXT"),
        ("away_team_id", "TEXT"),
        ("team_side", "TEXT"),
        ("target_team_id", "TEXT"),
        ("opponent_team_id", "TEXT"),
        ("home_team", "TEXT"),
        ("away_team", "TEXT"),
        ("selection", "TEXT"),
        ("book", "TEXT"),
        ("scheduled_kickoff_time", "TEXT"),
        ("decision_cutoff_time", "TEXT"),
        ("cutoff_policy_version", "TEXT"),
        ("point_in_time_status", "TEXT"),
        ("predictor_outcome_separation_status", "TEXT"),
        ("decision_readiness_status", "TEXT"),
        ("signal_usage_mode", "TEXT"),
        ("signal_id", "TEXT"),
        ("signal_name", "TEXT"),
        ("signal_family", "TEXT"),
        ("signal_version", "TEXT"),
        ("classification", "TEXT"),
        ("value_type", "TEXT"),
        ("unit", "TEXT"),
        ("signal_owner", "TEXT"),
        ("entity_scope", "TEXT"),
        ("dataset_grain_compatibility", "TEXT"),
        ("transformation_version", "TEXT"),
        ("missingness_policy", "TEXT"),
        ("signal_context_id", "TEXT"),
        ("signal_value_json", "TEXT"),
        ("signal_value_text", "TEXT"),
        ("signal_value_number", "REAL"),
        ("signal_value_boolean", "INTEGER"),
        ("signal_missingness_state", "TEXT"),
        ("signal_missingness_reason", "TEXT"),
        ("signal_definition_json", "TEXT"),
        ("signal_context_json", "TEXT"),
        ("signal_snapshot_grain_id", "TEXT"),
        ("signal_registry_schema_version", "TEXT"),
        ("signal_lineage_id", "TEXT"),
        ("signal_evidence_id", "TEXT"),
        ("source_feature_ids_json", "TEXT"),
        ("source_feature_snapshot_ids_json", "TEXT"),
        ("source_feature_lineage_ids_json", "TEXT"),
        ("source_feature_certification_ids_json", "TEXT"),
        ("source_feature_dataset_certification_ids_json", "TEXT"),
        ("source_feature_alignment_certification_ids_json", "TEXT"),
        ("source_feature_missingness_json", "TEXT"),
        ("source_feature_freshness_json", "TEXT"),
        ("source_feature_value_types_json", "TEXT"),
        ("source_feature_values_json", "TEXT"),
        ("source_math_output_ids_json", "TEXT"),
        ("source_math_snapshot_ids_json", "TEXT"),
        ("source_math_lineage_ids_json", "TEXT"),
        ("source_math_certification_ids_json", "TEXT"),
        ("source_math_dataset_certification_ids_json", "TEXT"),
        ("source_math_missingness_json", "TEXT"),
        ("source_math_freshness_json", "TEXT"),
        ("source_math_value_types_json", "TEXT"),
        ("source_math_values_json", "TEXT"),
        ("missing_required_assets_json", "TEXT"),
        ("evidence_package_id", "TEXT"),
        ("record_count", "INTEGER"),
        ("signal_count", "INTEGER"),
        ("signal_values_json", "TEXT"),
        ("summary_json", "TEXT"),
        ("payload_json", "TEXT"),
        *columns,
    ]


def _decision_columns(*columns: tuple[str, str]) -> list[tuple[str, str]]:
    transformed: list[tuple[str, str]] = []
    for name, column_type in _signal_columns():
        if name == "signal_pack":
            transformed.append(("decision_pack", column_type))
        elif name == "signal_pack_version":
            transformed.append(("decision_pack_version", column_type))
        elif name == "signal_usage_mode":
            transformed.append(("decision_usage_mode", column_type))
        elif name == "signal_id":
            transformed.append(("decision_id", column_type))
        elif name == "signal_name":
            transformed.append(("decision_name", column_type))
        elif name == "signal_family":
            transformed.append(("decision_family", column_type))
        elif name == "signal_version":
            transformed.append(("decision_version", column_type))
        elif name == "signal_owner":
            transformed.append(("decision_owner", column_type))
        elif name == "signal_context_id":
            transformed.append(("decision_snapshot_context_id", column_type))
        elif name == "signal_value_json":
            transformed.append(("decision_value_json", column_type))
        elif name == "signal_value_text":
            transformed.append(("decision_value_text", column_type))
        elif name == "signal_value_number":
            transformed.append(("decision_value_number", column_type))
        elif name == "signal_value_boolean":
            transformed.append(("decision_value_boolean", column_type))
        elif name == "signal_missingness_state":
            transformed.append(("decision_missingness_state", column_type))
        elif name == "signal_missingness_reason":
            transformed.append(("decision_missingness_reason", column_type))
        elif name == "signal_definition_json":
            transformed.append(("decision_definition_json", column_type))
        elif name == "signal_context_json":
            transformed.append(("decision_context_json", column_type))
        elif name == "signal_snapshot_grain_id":
            transformed.append(("decision_snapshot_grain_id", column_type))
        elif name == "signal_registry_schema_version":
            transformed.append(("decision_registry_schema_version", column_type))
        elif name == "signal_lineage_id":
            transformed.append(("decision_lineage_id", column_type))
        elif name == "signal_evidence_id":
            transformed.append(("decision_evidence_id", column_type))
        elif name == "signal_count":
            transformed.append(("decision_count", column_type))
        elif name == "signal_values_json":
            transformed.append(("decision_values_json", column_type))
        elif name == "source_math_values_json":
            transformed.append((name, column_type))
            transformed.extend(
                [
                    ("source_signal_context_id", "TEXT"),
                    ("source_signal_dataset_id", "TEXT"),
                    ("source_signal_dataset_name", "TEXT"),
                    ("source_signal_batch_id", "TEXT"),
                    ("source_signal_version_id", "TEXT"),
                    ("source_signal_certification_id", "TEXT"),
                    ("source_signal_dataset_certification_id", "TEXT"),
                    ("source_signal_population_summary_id", "TEXT"),
                    ("source_signal_evidence_package_id", "TEXT"),
                    ("source_signal_batch_lineage_id", "TEXT"),
                    ("source_signal_row_count", "INTEGER"),
                    ("source_signal_snapshot_count", "INTEGER"),
                    ("source_signal_definition_count", "INTEGER"),
                    ("source_signal_ids_json", "TEXT"),
                    ("source_signal_snapshot_ids_json", "TEXT"),
                    ("source_signal_lineage_ids_json", "TEXT"),
                    ("source_signal_certification_ids_json", "TEXT"),
                    ("source_signal_dataset_certification_ids_json", "TEXT"),
                    ("source_signal_alignment_certification_ids_json", "TEXT"),
                    ("source_signal_missingness_json", "TEXT"),
                    ("source_signal_freshness_json", "TEXT"),
                    ("source_signal_value_types_json", "TEXT"),
                    ("source_signal_values_json", "TEXT"),
                ]
            )
        else:
            transformed.append((name, column_type))
    return [*transformed, *columns]


def _nfl_p0_columns(*columns: tuple[str, str]) -> list[tuple[str, str]]:
    return [
        ("dataset_version", "TEXT"),
        ("source_name", "TEXT"),
        ("source_type", "TEXT"),
        ("source_snapshot_time", "TEXT"),
        ("snapshot_time", "TEXT"),
        ("decision_time", "TEXT"),
        ("status", "TEXT"),
        ("completeness_score", "REAL"),
        ("payload_json", "TEXT"),
        ("source_metadata_json", "TEXT"),
        *columns,
    ]


def _backtest_row_columns(*columns: tuple[str, str]) -> list[tuple[str, str]]:
    return [
        ("backtest_run_id", "TEXT"),
        ("decision_dataset_id", "TEXT"),
        ("decision_batch_id", "TEXT"),
        ("source_decision_snapshot_id", "TEXT"),
        ("source_decision_context_id", "TEXT"),
        ("source_signal_context_id", "TEXT"),
        ("source_dataset_snapshot_id", "TEXT"),
        ("source_dataset_lineage_id", "TEXT"),
        ("dataset_row_id", "TEXT"),
        ("event_id", "TEXT"),
        ("game_id", "TEXT"),
        ("season", "INTEGER"),
        ("week", "INTEGER"),
        ("market_type", "TEXT"),
        ("selection", "TEXT"),
        ("book", "TEXT"),
        ("home_team_id", "TEXT"),
        ("away_team_id", "TEXT"),
        ("target_team_id", "TEXT"),
        ("opponent_team_id", "TEXT"),
        ("decision_cutoff_time", "TEXT"),
        ("scheduled_kickoff_time", "TEXT"),
        ("settlement_recorded_time", "TEXT"),
        ("decision_readiness_status", "TEXT"),
        ("replay_status", "TEXT"),
        ("rejection_reason", "TEXT"),
        ("point_in_time_valid", "INTEGER"),
        ("point_in_time_validation_json", "TEXT"),
        ("settlement_status", "TEXT"),
        ("outcome_status", "TEXT"),
        ("actual_outcome", "REAL"),
        ("push_flag", "INTEGER"),
        ("stake_units", "REAL"),
        ("profit_loss_units", "REAL"),
        ("roi_percent", "REAL"),
        ("line_value", "REAL"),
        ("american_odds", "REAL"),
        ("decimal_odds", "REAL"),
        ("market_implied_probability", "REAL"),
        ("consensus_probability", "REAL"),
        ("pricing_gap", "REAL"),
        ("fair_american_odds", "REAL"),
        ("fair_decimal_odds", "REAL"),
        ("confidence_score", "REAL"),
        ("confidence_grade", "TEXT"),
        ("benchmark_no_trade_profit_loss_units", "REAL"),
        ("benchmark_market_expected_profit_loss_units", "REAL"),
        ("benchmark_market_brier_score", "REAL"),
        ("benchmark_market_log_loss", "REAL"),
        ("payload_json", "TEXT"),
        *columns,
    ]


def _nfl_game_context_columns(*columns: tuple[str, str]) -> list[tuple[str, str]]:
    return [
        ("game_id", "TEXT"),
        ("season", "INTEGER"),
        ("season_type", "TEXT"),
        ("week", "INTEGER"),
        ("game_date", "TEXT"),
        ("kickoff_time", "TEXT"),
        ("home_team_id", "TEXT"),
        ("home_team", "TEXT"),
        ("away_team_id", "TEXT"),
        ("away_team", "TEXT"),
        ("venue_id", "TEXT"),
        ("venue_name", "TEXT"),
        ("venue_city", "TEXT"),
        ("venue_state", "TEXT"),
        ("neutral_site", "INTEGER"),
        *columns,
    ]


def _historical_stage_columns(*columns: tuple[str, str]) -> list[tuple[str, str]]:
    return [
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("market_profile", "TEXT"),
        ("profile_id", "TEXT"),
        ("profile_family", "TEXT"),
        ("stage_name", "TEXT"),
        ("batch_id", "TEXT"),
        ("source_name", "TEXT"),
        ("source_type", "TEXT"),
        ("source_key", "TEXT"),
        ("source_file", "TEXT"),
        ("source_event_id", "TEXT"),
        ("source_market_id", "TEXT"),
        ("source_selection_id", "TEXT"),
        ("source_snapshot_time", "TEXT"),
        ("snapshot_time", "TEXT"),
        ("decision_time", "TEXT"),
        ("certified_at", "TEXT"),
        ("certification_status", "TEXT"),
        ("point_in_time_status", "TEXT"),
        ("leakage_status", "TEXT"),
        ("status", "TEXT"),
        ("completeness_score", "REAL"),
        ("source_metadata_json", "TEXT"),
        ("context_json", "TEXT"),
        ("payload_json", "TEXT"),
        *columns,
    ]


TABLE_DEFINITIONS: dict[str, list[tuple[str, str]]] = {
    "dataset_registry": [
        ("dataset_id", "TEXT PRIMARY KEY"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("latest_version_number", "INTEGER"),
        ("latest_snapshot_id", "TEXT"),
        ("latest_feature_snapshot_id", "TEXT"),
        ("latest_validation_id", "TEXT"),
        ("version_count", "INTEGER"),
        ("deprecated_at", "TEXT"),
        ("deprecated_reason", "TEXT"),
        ("metadata_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "dataset_versions": [
        ("version_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("version_number", "INTEGER"),
        ("raw_record_count", "INTEGER"),
        ("normalized_record_count", "INTEGER"),
        ("feature_snapshot_count", "INTEGER"),
        ("validation_id", "TEXT"),
        ("checksum", "TEXT"),
        ("metadata_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "raw_records": [
        ("record_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("row_index", "INTEGER"),
        ("payload_json", "TEXT"),
    ],
    "normalized_records": [
        ("record_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("row_index", "INTEGER"),
        ("raw_record_id", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "feature_snapshots": [
        ("snapshot_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("batch_id", "TEXT"),
        ("snapshot_kind", "TEXT"),
        ("feature_pack_version", "TEXT"),
        ("dataset_batch_id", "TEXT"),
        ("dataset_version_id", "TEXT"),
        ("dataset_row_id", "TEXT"),
        ("decision_context_id", "TEXT"),
        ("event_id", "TEXT"),
        ("game_id", "TEXT"),
        ("season", "INTEGER"),
        ("week", "INTEGER"),
        ("home_team_id", "TEXT"),
        ("away_team_id", "TEXT"),
        ("team_side", "TEXT"),
        ("target_team_id", "TEXT"),
        ("opponent_team_id", "TEXT"),
        ("home_team", "TEXT"),
        ("away_team", "TEXT"),
        ("market_type", "TEXT"),
        ("selection", "TEXT"),
        ("book", "TEXT"),
        ("scheduled_kickoff_time", "TEXT"),
        ("decision_cutoff_time", "TEXT"),
        ("cutoff_policy_version", "TEXT"),
        ("feature_id", "TEXT"),
        ("feature_name", "TEXT"),
        ("feature_family", "TEXT"),
        ("feature_version", "TEXT"),
        ("classification", "TEXT"),
        ("value_type", "TEXT"),
        ("unit", "TEXT"),
        ("feature_owner", "TEXT"),
        ("entity_scope", "TEXT"),
        ("dataset_grain_compatibility", "TEXT"),
        ("transformation_version", "TEXT"),
        ("missingness_policy", "TEXT"),
        ("feature_context_id", "TEXT"),
        ("feature_value_json", "TEXT"),
        ("feature_value_text", "TEXT"),
        ("feature_value_number", "REAL"),
        ("feature_value_boolean", "INTEGER"),
        ("feature_missingness_state", "TEXT"),
        ("feature_missingness_reason", "TEXT"),
        ("feature_definition_json", "TEXT"),
        ("feature_context_json", "TEXT"),
        ("feature_snapshot_grain_id", "TEXT"),
        ("feature_registry_schema_version", "TEXT"),
        ("source_dataset_batch_id", "TEXT"),
        ("source_dataset_row_count", "INTEGER"),
        ("certification_id", "TEXT"),
        ("dataset_certification_id", "TEXT"),
        ("feature_lineage_id", "TEXT"),
        ("feature_evidence_id", "TEXT"),
        ("source_certification_ids_json", "TEXT"),
        ("source_alignment_certification_ids_json", "TEXT"),
        ("selected_source_row_ids_json", "TEXT"),
        ("source_lineage_ids_json", "TEXT"),
        ("predictor_references_json", "TEXT"),
        ("missing_required_assets_json", "TEXT"),
        ("asset_freshness_json", "TEXT"),
        ("evidence_package_id", "TEXT"),
        ("record_count", "INTEGER"),
        ("feature_count", "INTEGER"),
        ("feature_values_json", "TEXT"),
        ("summary_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "math_engine_snapshots": _math_engine_columns(),
    "signal_snapshots": _signal_columns(),
    "decision_rows": _decision_columns(),
    "lineage_edges": [
        ("lineage_edge_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("source_stage", "TEXT"),
        ("source_id", "TEXT"),
        ("target_stage", "TEXT"),
        ("target_id", "TEXT"),
        ("transformation", "TEXT"),
        ("step_index", "INTEGER"),
        ("payload_json", "TEXT"),
    ],
    "validation_results": [
        ("validation_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("validation_passed", "INTEGER"),
        ("error_count", "INTEGER"),
        ("warning_count", "INTEGER"),
        ("missing_fields_json", "TEXT"),
        ("duplicate_keys_json", "TEXT"),
        ("join_keys_json", "TEXT"),
        ("validation_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "provider_metadata": [
        ("provider_id", "TEXT PRIMARY KEY"),
        ("provider_name", "TEXT"),
        ("provider_type", "TEXT"),
        ("contract_version", "TEXT"),
        ("metadata_json", "TEXT"),
    ],
    "nfl_games": _nfl_p0_columns(
        ("game_id", "TEXT PRIMARY KEY"),
        ("season", "INTEGER"),
        ("season_type", "TEXT"),
        ("week", "INTEGER"),
        ("game_date", "TEXT"),
        ("kickoff_time", "TEXT"),
        ("home_team_id", "TEXT"),
        ("home_team", "TEXT"),
        ("away_team_id", "TEXT"),
        ("away_team", "TEXT"),
        ("venue_id", "TEXT"),
        ("venue_name", "TEXT"),
        ("venue_city", "TEXT"),
        ("venue_state", "TEXT"),
        ("neutral_site", "INTEGER"),
        ("market_type", "TEXT"),
        ("finalization_status", "TEXT"),
        ("source_signature", "TEXT"),
    ),
    "nfl_schedule": _nfl_p0_columns(
        ("schedule_id", "TEXT PRIMARY KEY"),
        *_nfl_game_context_columns(),
        ("game_state", "TEXT"),
        ("schedule_status", "TEXT"),
        ("market_type", "TEXT"),
        ("source_signature", "TEXT"),
    ),
    "nfl_results": _nfl_p0_columns(
        ("result_id", "TEXT PRIMARY KEY"),
        *_nfl_game_context_columns(),
        ("game_time", "TEXT"),
        ("final_scored_at", "TEXT"),
        ("final_score_home", "INTEGER"),
        ("final_score_away", "INTEGER"),
        ("winner_team_id", "TEXT"),
        ("winner_team", "TEXT"),
        ("margin", "INTEGER"),
        ("total_points", "INTEGER"),
        ("settlement_status", "TEXT"),
        ("finalization_status", "TEXT"),
        ("source_signature", "TEXT"),
    ),
    "nfl_odds_snapshots": _nfl_p0_columns(
        ("odds_snapshot_id", "TEXT PRIMARY KEY"),
        *_nfl_game_context_columns(),
        ("book", "TEXT"),
        ("market", "TEXT"),
        ("selection", "TEXT"),
        ("line_value", "REAL"),
        ("american_odds", "REAL"),
        ("decimal_odds", "REAL"),
        ("implied_probability", "REAL"),
        ("market_label", "TEXT"),
        ("freshness_score", "REAL"),
        ("source_signature", "TEXT"),
    ),
    "nfl_weather_snapshots": _nfl_p0_columns(
        ("weather_snapshot_id", "TEXT PRIMARY KEY"),
        *_nfl_game_context_columns(),
        ("forecast_time", "TEXT"),
        ("weather_condition", "TEXT"),
        ("temperature_f", "REAL"),
        ("wind_mph", "REAL"),
        ("wind_gust_mph", "REAL"),
        ("precipitation_pct", "REAL"),
        ("humidity_pct", "REAL"),
        ("pressure_hpa", "REAL"),
        ("indoor_flag", "INTEGER"),
        ("forecast_freshness", "REAL"),
        ("source_signature", "TEXT"),
    ),
    "nfl_injury_snapshots": _nfl_p0_columns(
        ("injury_snapshot_id", "TEXT PRIMARY KEY"),
        *_nfl_game_context_columns(),
        ("team_id", "TEXT"),
        ("team_name", "TEXT"),
        ("opponent_team_id", "TEXT"),
        ("player_id", "TEXT"),
        ("player_name", "TEXT"),
        ("position", "TEXT"),
        ("report_status", "TEXT"),
        ("availability_status", "TEXT"),
        ("practice_status", "TEXT"),
        ("report_primary_injury", "TEXT"),
        ("injury_category", "TEXT"),
        ("report_time", "TEXT"),
        ("timing_confidence", "REAL"),
        ("report_source", "TEXT"),
        ("source_signature", "TEXT"),
    ),
    "nfl_team_stats_snapshots": _nfl_p0_columns(
        ("team_stats_snapshot_id", "TEXT PRIMARY KEY"),
        *_nfl_game_context_columns(),
        ("team_id", "TEXT"),
        ("team_name", "TEXT"),
        ("opponent_team_id", "TEXT"),
        ("team_side", "TEXT"),
        ("source_record_id", "TEXT"),
        ("source_retrieved_at", "TEXT"),
        ("measurement_period", "TEXT"),
        ("statistic_context", "TEXT"),
        ("statistic_window_type", "TEXT"),
        ("window_start_time", "TEXT"),
        ("team_stats_cutoff_time", "TEXT"),
        ("window_excludes_current_event", "INTEGER"),
        ("rest_days", "REAL"),
        ("travel_distance_miles", "REAL"),
        ("travel_timezone_change", "REAL"),
        ("offensive_efficiency", "REAL"),
        ("defensive_efficiency", "REAL"),
        ("pace", "REAL"),
        ("play_volume", "REAL"),
        ("scoring_efficiency", "REAL"),
        ("turnover_rate", "REAL"),
        ("red_zone_efficiency", "REAL"),
        ("third_down_efficiency", "REAL"),
        ("special_teams_efficiency", "REAL"),
        ("coaching_continuity", "REAL"),
        ("roster_continuity", "REAL"),
        ("injury_adjusted_availability", "REAL"),
        ("position_group", "TEXT"),
        ("efficiency_window_games", "INTEGER"),
        ("metric_units_json", "TEXT"),
        ("field_provenance_json", "TEXT"),
        ("alignment_status", "TEXT"),
        ("certification_state", "TEXT"),
        ("source_signature", "TEXT"),
    ),
    "historical_acquisition_batches": _historical_stage_columns(
        ("batch_id", "TEXT PRIMARY KEY"),
        ("acquisition_started_at", "TEXT"),
        ("acquisition_completed_at", "TEXT"),
        ("source_count", "INTEGER"),
        ("event_count", "INTEGER"),
        ("market_count", "INTEGER"),
        ("selection_count", "INTEGER"),
        ("certified_row_count", "INTEGER"),
        ("rejected_row_count", "INTEGER"),
        ("coverage_json", "TEXT"),
        ("licensing_json", "TEXT"),
        ("provenance_json", "TEXT"),
        ("notes_json", "TEXT"),
    ),
    "historical_events": _historical_stage_columns(
        ("event_id", "TEXT PRIMARY KEY"),
        ("event_key", "TEXT"),
        ("sport", "TEXT"),
        ("league", "TEXT"),
        ("season", "INTEGER"),
        ("season_type", "TEXT"),
        ("week", "INTEGER"),
        ("game_id", "TEXT"),
        ("event_date", "TEXT"),
        ("event_start_time", "TEXT"),
        ("home_team", "TEXT"),
        ("away_team", "TEXT"),
        ("venue_id", "TEXT"),
        ("venue_name", "TEXT"),
        ("venue_city", "TEXT"),
        ("venue_state", "TEXT"),
        ("neutral_site", "INTEGER"),
        ("final_result", "TEXT"),
        ("final_score_home", "INTEGER"),
        ("final_score_away", "INTEGER"),
        ("winner_team", "TEXT"),
        ("margin", "INTEGER"),
        ("total_points", "INTEGER"),
        ("result_recorded_time", "TEXT"),
        ("result_status", "TEXT"),
        ("settlement_status", "TEXT"),
    ),
    "historical_markets": _historical_stage_columns(
        ("market_id", "TEXT PRIMARY KEY"),
        ("event_id", "TEXT"),
        ("event_start_time", "TEXT"),
        ("market_family", "TEXT"),
        ("market_type", "TEXT"),
        ("market_name", "TEXT"),
        ("book", "TEXT"),
        ("line_value", "REAL"),
        ("odds", "REAL"),
        ("opening_odds", "REAL"),
        ("closing_odds", "REAL"),
        ("price_type", "TEXT"),
        ("market_label", "TEXT"),
        ("selection_count", "INTEGER"),
    ),
    "historical_selections": _historical_stage_columns(
        ("selection_id", "TEXT PRIMARY KEY"),
        ("event_id", "TEXT"),
        ("event_start_time", "TEXT"),
        ("market_id", "TEXT"),
        ("market_family", "TEXT"),
        ("market_type", "TEXT"),
        ("market_name", "TEXT"),
        ("book", "TEXT"),
        ("selection", "TEXT"),
        ("selection_side", "TEXT"),
        ("line_value", "REAL"),
        ("odds", "REAL"),
        ("opening_odds", "REAL"),
        ("closing_odds", "REAL"),
        ("price_type", "TEXT"),
        ("market_label", "TEXT"),
        ("selection_count", "INTEGER"),
    ),
    "historical_certifications": _historical_stage_columns(
        ("certification_id", "TEXT PRIMARY KEY"),
        ("stage_name", "TEXT"),
        ("row_count", "INTEGER"),
        ("valid_row_count", "INTEGER"),
        ("invalid_row_count", "INTEGER"),
        ("warning_count", "INTEGER"),
        ("missing_fields_json", "TEXT"),
        ("duplicate_keys_json", "TEXT"),
        ("join_keys_json", "TEXT"),
        ("validation_json", "TEXT"),
    ),
    "historical_dataset_batches": _historical_stage_columns(
        ("batch_id", "TEXT PRIMARY KEY"),
        ("dataset_contract_version", "TEXT"),
        ("population_version", "TEXT"),
        ("dataset_as_of_time", "TEXT"),
        ("cutoff_policy_id", "TEXT"),
        ("cutoff_policy_version", "TEXT"),
        ("join_policy_id", "TEXT"),
        ("event_scope_json", "TEXT"),
        ("required_source_asset_ids_json", "TEXT"),
        ("source_asset_version_ids_json", "TEXT"),
        ("source_asset_batch_ids_json", "TEXT"),
        ("source_certification_ids_json", "TEXT"),
        ("source_dataset_certification_ids_json", "TEXT"),
        ("source_lifecycle_states_json", "TEXT"),
        ("source_alignment_counts_json", "TEXT"),
        ("source_record_counts_json", "TEXT"),
        ("eligible_record_counts_json", "TEXT"),
        ("selected_record_counts_json", "TEXT"),
        ("rejected_record_counts_json", "TEXT"),
        ("unmatched_record_counts_json", "TEXT"),
        ("join_diagnostics_json", "TEXT"),
        ("rejected_evidence_json", "TEXT"),
        ("unmatched_evidence_json", "TEXT"),
        ("cardinality_contract_json", "TEXT"),
        ("cardinality_validation_status", "TEXT"),
        ("point_in_time_validation_status", "TEXT"),
        ("predictor_outcome_separation_status", "TEXT"),
        ("provenance_completeness", "INTEGER"),
        ("lineage_completeness", "INTEGER"),
        ("dataset_row_count", "INTEGER"),
        ("rejected_row_count", "INTEGER"),
        ("unmatched_row_count", "INTEGER"),
        ("duplicate_row_count", "INTEGER"),
        ("evidence_package_id", "TEXT"),
        ("evidence_package_json", "TEXT"),
        ("readiness_state", "TEXT"),
        ("unresolved_blockers_json", "TEXT"),
    ),
    "historical_dataset_rows": _historical_stage_columns(
        ("dataset_row_id", "TEXT PRIMARY KEY"),
        ("decision_context_id", "TEXT"),
        ("schedule_id", "TEXT"),
        ("result_id", "TEXT"),
        ("odds_snapshot_id", "TEXT"),
        ("weather_snapshot_id", "TEXT"),
        ("home_team_stats_snapshot_id", "TEXT"),
        ("away_team_stats_snapshot_id", "TEXT"),
        ("event_id", "TEXT"),
        ("game_id", "TEXT"),
        ("season", "INTEGER"),
        ("season_type", "TEXT"),
        ("week", "INTEGER"),
        ("scheduled_kickoff_time", "TEXT"),
        ("event_start_time", "TEXT"),
        ("decision_cutoff_time", "TEXT"),
        ("cutoff_policy_version", "TEXT"),
        ("home_team_id", "TEXT"),
        ("home_team", "TEXT"),
        ("away_team_id", "TEXT"),
        ("away_team", "TEXT"),
        ("neutral_site", "INTEGER"),
        ("target_team_id", "TEXT"),
        ("target_team", "TEXT"),
        ("opponent_team_id", "TEXT"),
        ("opponent_team", "TEXT"),
        ("team_side", "TEXT"),
        ("book", "TEXT"),
        ("market_name", "TEXT"),
        ("market_type", "TEXT"),
        ("selection", "TEXT"),
        ("line_value", "REAL"),
        ("american_odds", "REAL"),
        ("decimal_odds", "REAL"),
        ("implied_probability", "REAL"),
        ("market_label", "TEXT"),
        ("price_type", "TEXT"),
        ("selected_odds_timestamp", "TEXT"),
        ("weather_forecast_time", "TEXT"),
        ("selected_weather_timestamp", "TEXT"),
        ("selected_home_injury_timestamp", "TEXT"),
        ("selected_away_injury_timestamp", "TEXT"),
        ("selected_home_team_stats_timestamp", "TEXT"),
        ("selected_away_team_stats_timestamp", "TEXT"),
        ("odds_freshness_seconds", "INTEGER"),
        ("weather_freshness_seconds", "INTEGER"),
        ("home_injury_freshness_seconds", "INTEGER"),
        ("away_injury_freshness_seconds", "INTEGER"),
        ("home_team_stats_freshness_seconds", "INTEGER"),
        ("away_team_stats_freshness_seconds", "INTEGER"),
        ("home_injury_record_count", "INTEGER"),
        ("away_injury_record_count", "INTEGER"),
        ("home_injury_row_ids_json", "TEXT"),
        ("away_injury_row_ids_json", "TEXT"),
        ("selected_source_row_ids_json", "TEXT"),
        ("source_lineage_ids_json", "TEXT"),
        ("asset_freshness_json", "TEXT"),
        ("missing_required_assets_json", "TEXT"),
        ("source_certification_ids_json", "TEXT"),
        ("source_dataset_certification_ids_json", "TEXT"),
        ("source_alignment_certification_ids_json", "TEXT"),
        ("predictor_references_json", "TEXT"),
        ("label_final_result", "TEXT"),
        ("label_final_score_home", "INTEGER"),
        ("label_final_score_away", "INTEGER"),
        ("label_winner_team_id", "TEXT"),
        ("label_winner_team", "TEXT"),
        ("label_margin", "INTEGER"),
        ("label_total_points", "INTEGER"),
        ("label_settlement_status", "TEXT"),
        ("label_result_recorded_time", "TEXT"),
        ("predictor_outcome_separation_status", "TEXT"),
        ("evidence_package_id", "TEXT"),
        ("evidence_package_json", "TEXT"),
        ("decision_readiness_status", "TEXT"),
        ("readiness_state", "TEXT"),
        ("unresolved_blockers_json", "TEXT"),
    ),
    "historical_research_asset_certifications": _historical_stage_columns(
        ("certification_id", "TEXT PRIMARY KEY"),
        ("research_asset_id", "TEXT"),
        ("research_asset_name", "TEXT"),
        ("asset_category", "TEXT"),
        ("asset_type", "TEXT"),
        ("asset_version", "TEXT"),
        ("certification_version", "TEXT"),
        ("certification_state", "TEXT"),
        ("certification_reason", "TEXT"),
        ("failure_reason", "TEXT"),
        ("coverage_score", "REAL"),
        ("certification_score", "REAL"),
        ("required_fields_json", "TEXT"),
        ("required_timestamps_json", "TEXT"),
        ("point_in_time_rules_json", "TEXT"),
        ("validation_json", "TEXT"),
        ("lineage_json", "TEXT"),
        ("provenance_json", "TEXT"),
        ("certification_notes_json", "TEXT"),
        ("missing_fields_json", "TEXT"),
        ("duplicate_keys_json", "TEXT"),
        ("join_keys_json", "TEXT"),
        ("valid_row_count", "INTEGER"),
        ("invalid_row_count", "INTEGER"),
        ("warning_count", "INTEGER"),
        ("source_row_count", "INTEGER"),
        ("checksum", "TEXT"),
    ),
    "research_asset_lifecycles": _historical_stage_columns(
        ("asset_id", "TEXT PRIMARY KEY"),
        ("research_asset_id", "TEXT"),
        ("research_asset_name", "TEXT"),
        ("asset_family", "TEXT"),
        ("asset_type", "TEXT"),
        ("asset_name", "TEXT"),
        ("league", "TEXT"),
        ("sport", "TEXT"),
        ("season", "TEXT"),
        ("week_or_date", "TEXT"),
        ("event_id", "TEXT"),
        ("game_id", "TEXT"),
        ("market_id", "TEXT"),
        ("selection", "TEXT"),
        ("participant_id", "TEXT"),
        ("team_id", "TEXT"),
        ("connector", "TEXT"),
        ("lifecycle_state", "TEXT"),
        ("lifecycle_state_index", "INTEGER"),
        ("lifecycle_reason", "TEXT"),
        ("alignment_status", "TEXT"),
        ("alignment_reason", "TEXT"),
        ("alignment_score", "REAL"),
        ("alignment_certification_id", "TEXT"),
        ("certification_id", "TEXT"),
        ("state_history_json", "TEXT"),
        ("transition_history_json", "TEXT"),
        ("identity_json", "TEXT"),
        ("alignment_json", "TEXT"),
        ("notes_json", "TEXT"),
    ),
    "research_asset_alignment_certifications": _historical_stage_columns(
        ("alignment_certification_id", "TEXT PRIMARY KEY"),
        ("asset_id", "TEXT"),
        ("research_asset_id", "TEXT"),
        ("research_asset_name", "TEXT"),
        ("asset_family", "TEXT"),
        ("asset_type", "TEXT"),
        ("connector", "TEXT"),
        ("market_profile", "TEXT"),
        ("market", "TEXT"),
        ("market_type", "TEXT"),
        ("league", "TEXT"),
        ("sport", "TEXT"),
        ("season", "TEXT"),
        ("week_or_date", "TEXT"),
        ("event_id", "TEXT"),
        ("game_id", "TEXT"),
        ("market_id", "TEXT"),
        ("selection", "TEXT"),
        ("participant_id", "TEXT"),
        ("team_id", "TEXT"),
        ("provider_timestamp", "TEXT"),
        ("snapshot_time", "TEXT"),
        ("decision_time", "TEXT"),
        ("result_timestamp", "TEXT"),
        ("alignment_status", "TEXT"),
        ("alignment_reason", "TEXT"),
        ("failure_reason", "TEXT"),
        ("alignment_score", "REAL"),
        ("missing_fields_json", "TEXT"),
        ("mismatched_fields_json", "TEXT"),
        ("timing_issues_json", "TEXT"),
        ("validation_json", "TEXT"),
        ("lineage_json", "TEXT"),
        ("provenance_json", "TEXT"),
        ("certification_notes_json", "TEXT"),
        ("row_count", "INTEGER"),
        ("source_row_count", "INTEGER"),
        ("checksum", "TEXT"),
        ("lineage_version", "TEXT"),
        ("certification_timestamp", "TEXT"),
    ),
    "model_runs": [
        ("model_run_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("model_name", "TEXT"),
        ("model_version", "TEXT"),
        ("metrics_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "backtest_runs": [
        ("backtest_run_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("strategy_name", "TEXT"),
        ("decision_batch_id", "TEXT"),
        ("source_decision_dataset_id", "TEXT"),
        ("source_decision_population_summary_id", "TEXT"),
        ("source_decision_dataset_certification_id", "TEXT"),
        ("source_decision_batch_lineage_id", "TEXT"),
        ("sample_size", "INTEGER"),
        ("wins", "INTEGER"),
        ("losses", "INTEGER"),
        ("pushes", "INTEGER"),
        ("profit_loss_units", "REAL"),
        ("roi_percent", "REAL"),
        ("point_in_time_ok", "INTEGER"),
        ("artifact_root", "TEXT"),
        ("report_json_path", "TEXT"),
        ("report_markdown_path", "TEXT"),
        ("dashboard_json_path", "TEXT"),
        ("results_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "backtest_rows": _backtest_row_columns(
        ("backtest_row_id", "TEXT PRIMARY KEY"),
    ),
    "research_intelligence_runs": [
        ("research_intelligence_run_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("pipeline_validation_run_id", "TEXT"),
        ("backtest_run_id", "TEXT"),
        ("decision_batch_id", "TEXT"),
        ("source_dataset_batch_id", "TEXT"),
        ("source_feature_batch_id", "TEXT"),
        ("source_math_batch_id", "TEXT"),
        ("source_signal_batch_id", "TEXT"),
        ("sample_size", "INTEGER"),
        ("wins", "INTEGER"),
        ("losses", "INTEGER"),
        ("pushes", "INTEGER"),
        ("profit_loss_units", "REAL"),
        ("roi_percent", "REAL"),
        ("opportunity_count", "INTEGER"),
        ("artifact_root", "TEXT"),
        ("report_json_path", "TEXT"),
        ("report_markdown_path", "TEXT"),
        ("dashboard_json_path", "TEXT"),
        ("results_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "research_intelligence_opportunities": [
        ("research_opportunity_id", "TEXT PRIMARY KEY"),
        ("research_intelligence_run_id", "TEXT"),
        ("evidence_package_id", "TEXT"),
        ("pipeline_validation_run_id", "TEXT"),
        ("backtest_run_id", "TEXT"),
        ("decision_batch_id", "TEXT"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("dataset_row_id", "TEXT"),
        ("event_id", "TEXT"),
        ("game_id", "TEXT"),
        ("season", "INTEGER"),
        ("week", "INTEGER"),
        ("market_type", "TEXT"),
        ("selection", "TEXT"),
        ("outcome_status", "TEXT"),
        ("profit_loss_units", "REAL"),
        ("roi_percent", "REAL"),
        ("confidence_score", "REAL"),
        ("confidence_grade", "TEXT"),
        ("signal_agreement_state", "TEXT"),
        ("feature_contribution_state", "TEXT"),
        ("market_implied_probability", "REAL"),
        ("consensus_probability", "REAL"),
        ("pricing_gap", "REAL"),
        ("historical_rank", "INTEGER"),
        ("evidence_rank", "INTEGER"),
        ("payload_json", "TEXT"),
        ("market_type_classification", "TEXT"),
    ],
    "nfl_production_completion_runs": [
        ("nfl_production_completion_run_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("research_intelligence_run_id", "TEXT"),
        ("universal_market_framework_run_id", "TEXT"),
        ("pipeline_validation_run_id", "TEXT"),
        ("backtest_run_id", "TEXT"),
        ("decision_batch_id", "TEXT"),
        ("audit_item_count", "INTEGER"),
        ("blocking_gap_count", "INTEGER"),
        ("warning_gap_count", "INTEGER"),
        ("dashboard_view_count", "INTEGER"),
        ("query_interface_count", "INTEGER"),
        ("artifact_root", "TEXT"),
        ("report_json_path", "TEXT"),
        ("report_markdown_path", "TEXT"),
        ("dashboard_json_path", "TEXT"),
        ("results_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "nfl_production_completion_audit_items": [
        ("audit_item_id", "TEXT PRIMARY KEY"),
        ("nfl_production_completion_run_id", "TEXT"),
        ("requirement_id", "TEXT"),
        ("requirement_name", "TEXT"),
        ("classification", "TEXT"),
        ("blocking_if_incomplete", "INTEGER"),
        ("status", "TEXT"),
        ("validation_state", "TEXT"),
        ("canonical_owner", "TEXT"),
        ("summary", "TEXT"),
        ("source_snapshot_ids_json", "TEXT"),
        ("source_artifact_paths_json", "TEXT"),
        ("lineage_reference_json", "TEXT"),
        ("details_json", "TEXT"),
    ],
    "identity_mappings": [
        ("mapping_id", "TEXT PRIMARY KEY"),
        ("internal_identifier", "TEXT"),
        ("external_identifier", "TEXT"),
        ("entity_type", "TEXT"),
        ("entity_name", "TEXT"),
        ("canonical_key", "TEXT"),
        ("mapping_status", "TEXT"),
        ("match_method", "TEXT"),
        ("confidence", "REAL"),
        ("review_state", "TEXT"),
        ("mapping_version", "TEXT"),
        ("approval_reference", "TEXT"),
        ("approval_evidence_json", "TEXT"),
        ("valid_from", "TEXT"),
        ("valid_to", "TEXT"),
        ("revision_number", "INTEGER"),
        ("is_latest", "INTEGER"),
        ("event_time", "TEXT"),
        ("published_at", "TEXT"),
        ("observed_at", "TEXT"),
        ("processed_at", "TEXT"),
        ("source_published_at", "TEXT"),
        ("system_observed_at", "TEXT"),
        ("lineage_reference_json", "TEXT"),
        ("source_payload_json", "TEXT"),
        ("notes_json", "TEXT"),
    ],
    "identity_match_candidates": [
        ("candidate_id", "TEXT PRIMARY KEY"),
        ("entity_type", "TEXT"),
        ("internal_identifier", "TEXT"),
        ("external_identifier", "TEXT"),
        ("candidate_internal_identifier", "TEXT"),
        ("candidate_name", "TEXT"),
        ("candidate_rank", "INTEGER"),
        ("match_method", "TEXT"),
        ("confidence", "REAL"),
        ("decision_status", "TEXT"),
        ("review_state", "TEXT"),
        ("reasons_json", "TEXT"),
        ("canonical_key", "TEXT"),
        ("event_time", "TEXT"),
        ("published_at", "TEXT"),
        ("observed_at", "TEXT"),
        ("processed_at", "TEXT"),
        ("source_published_at", "TEXT"),
        ("system_observed_at", "TEXT"),
        ("lineage_reference_json", "TEXT"),
        ("source_payload_json", "TEXT"),
    ],
    "identity_reconciliation_results": [
        ("reconciliation_id", "TEXT PRIMARY KEY"),
        ("reconciliation_scope", "TEXT"),
        ("entity_type", "TEXT"),
        ("internal_identifier", "TEXT"),
        ("external_identifier", "TEXT"),
        ("reconciliation_status", "TEXT"),
        ("decision_status", "TEXT"),
        ("decision_explanation", "TEXT"),
        ("freshness_seconds", "INTEGER"),
        ("timestamp_agreement_status", "TEXT"),
        ("outlier_status", "TEXT"),
        ("quality_score", "REAL"),
        ("accepted_evidence_json", "TEXT"),
        ("rejected_evidence_json", "TEXT"),
        ("provider_reliability_json", "TEXT"),
        ("observation_identity_json", "TEXT"),
        ("event_time", "TEXT"),
        ("published_at", "TEXT"),
        ("observed_at", "TEXT"),
        ("processed_at", "TEXT"),
        ("source_published_at", "TEXT"),
        ("system_observed_at", "TEXT"),
        ("valid_from", "TEXT"),
        ("valid_to", "TEXT"),
        ("revision_number", "INTEGER"),
        ("is_latest", "INTEGER"),
        ("lineage_reference_json", "TEXT"),
        ("source_payload_json", "TEXT"),
    ],
    "data_quality_events": [
        ("quality_event_id", "TEXT PRIMARY KEY"),
        ("dataset_table", "TEXT"),
        ("record_identifier", "TEXT"),
        ("entity_type", "TEXT"),
        ("internal_identifier", "TEXT"),
        ("external_identifier", "TEXT"),
        ("quality_event_type", "TEXT"),
        ("severity", "TEXT"),
        ("decision_status", "TEXT"),
        ("decision_explanation", "TEXT"),
        ("review_state", "TEXT"),
        ("event_time", "TEXT"),
        ("published_at", "TEXT"),
        ("observed_at", "TEXT"),
        ("processed_at", "TEXT"),
        ("source_published_at", "TEXT"),
        ("system_observed_at", "TEXT"),
        ("details_json", "TEXT"),
        ("lineage_reference_json", "TEXT"),
        ("source_payload_json", "TEXT"),
    ],
    "quarantine_records": [
        ("quarantine_id", "TEXT PRIMARY KEY"),
        ("dataset_table", "TEXT"),
        ("record_identifier", "TEXT"),
        ("entity_type", "TEXT"),
        ("internal_identifier", "TEXT"),
        ("external_identifier", "TEXT"),
        ("quarantine_reason", "TEXT"),
        ("decision_status", "TEXT"),
        ("review_state", "TEXT"),
        ("release_state", "TEXT"),
        ("match_candidate_ids_json", "TEXT"),
        ("event_time", "TEXT"),
        ("published_at", "TEXT"),
        ("observed_at", "TEXT"),
        ("processed_at", "TEXT"),
        ("source_published_at", "TEXT"),
        ("system_observed_at", "TEXT"),
        ("details_json", "TEXT"),
        ("lineage_reference_json", "TEXT"),
        ("source_payload_json", "TEXT"),
    ],
    "manual_review_queue": [
        ("review_id", "TEXT PRIMARY KEY"),
        ("entity_type", "TEXT"),
        ("internal_identifier", "TEXT"),
        ("external_identifier", "TEXT"),
        ("review_state", "TEXT"),
        ("decision_status", "TEXT"),
        ("priority", "TEXT"),
        ("recommended_action", "TEXT"),
        ("candidate_ids_json", "TEXT"),
        ("approval_reference", "TEXT"),
        ("opened_at", "TEXT"),
        ("closed_at", "TEXT"),
        ("details_json", "TEXT"),
        ("lineage_reference_json", "TEXT"),
        ("source_payload_json", "TEXT"),
    ],
    "mapping_approvals": [
        ("approval_id", "TEXT PRIMARY KEY"),
        ("mapping_id", "TEXT"),
        ("internal_identifier", "TEXT"),
        ("external_identifier", "TEXT"),
        ("entity_type", "TEXT"),
        ("approval_state", "TEXT"),
        ("approval_role", "TEXT"),
        ("approval_reference", "TEXT"),
        ("approval_evidence_json", "TEXT"),
        ("approved_at", "TEXT"),
        ("valid_from", "TEXT"),
        ("valid_to", "TEXT"),
        ("details_json", "TEXT"),
    ],
    "lakehouse_partitions": [
        ("partition_id", "TEXT PRIMARY KEY"),
        ("layer_name", "TEXT"),
        ("dataset_table", "TEXT"),
        ("dataset_identifier", "TEXT"),
        ("market_profile", "TEXT"),
        ("partition_key_json", "TEXT"),
        ("partition_values_json", "TEXT"),
        ("partition_columns_json", "TEXT"),
        ("file_path", "TEXT"),
        ("deterministic_file_id", "TEXT"),
        ("content_digest", "TEXT"),
        ("file_checksum", "TEXT"),
        ("schema_version", "TEXT"),
        ("row_count", "INTEGER"),
        ("file_size_bytes", "INTEGER"),
        ("delta_table_name", "TEXT"),
        ("delta_metadata_json", "TEXT"),
        ("compaction_group", "TEXT"),
        ("roundtrip_row_count", "INTEGER"),
        ("roundtrip_ok", "INTEGER"),
        ("metadata_json", "TEXT"),
    ],
    "data_identity_foundation_runs": [
        ("data_identity_foundation_run_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("nfl_production_completion_run_id", "TEXT"),
        ("universal_market_framework_run_id", "TEXT"),
        ("research_intelligence_run_id", "TEXT"),
        ("pipeline_validation_run_id", "TEXT"),
        ("backtest_run_id", "TEXT"),
        ("audit_item_count", "INTEGER"),
        ("blocking_gap_count", "INTEGER"),
        ("warning_gap_count", "INTEGER"),
        ("identity_mapping_count", "INTEGER"),
        ("reconciliation_result_count", "INTEGER"),
        ("lakehouse_partition_count", "INTEGER"),
        ("artifact_root", "TEXT"),
        ("report_json_path", "TEXT"),
        ("report_markdown_path", "TEXT"),
        ("dashboard_json_path", "TEXT"),
        ("results_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "data_identity_foundation_audit_items": [
        ("audit_item_id", "TEXT PRIMARY KEY"),
        ("data_identity_foundation_run_id", "TEXT"),
        ("requirement_id", "TEXT"),
        ("requirement_name", "TEXT"),
        ("initial_classification", "TEXT"),
        ("final_classification", "TEXT"),
        ("blocking_if_incomplete", "INTEGER"),
        ("status", "TEXT"),
        ("validation_state", "TEXT"),
        ("canonical_owner", "TEXT"),
        ("summary", "TEXT"),
        ("implemented_changes_json", "TEXT"),
        ("source_snapshot_ids_json", "TEXT"),
        ("source_artifact_paths_json", "TEXT"),
        ("lineage_reference_json", "TEXT"),
        ("details_json", "TEXT"),
    ],
    "research_runs": [
        ("research_run_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("study_name", "TEXT"),
        ("results_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "streamlit_layouts": [
        ("layout_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("page_name", "TEXT"),
        ("widget_name", "TEXT"),
        ("layout_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
    "audit_events": [
        ("event_id", "TEXT PRIMARY KEY"),
        ("dataset_id", "TEXT"),
        ("dataset_name", "TEXT"),
        ("owner", "TEXT"),
        ("sport", "TEXT"),
        ("feature_pack", "TEXT"),
        ("storage_location", "TEXT"),
        ("readiness", "TEXT"),
        ("update_frequency", "TEXT"),
        ("validation_state", "TEXT"),
        ("status", "TEXT"),
        ("event_type", "TEXT"),
        ("actor", "TEXT"),
        ("detail_json", "TEXT"),
        ("payload_json", "TEXT"),
    ],
}


def _build_create_table_sql(table_name: str, columns: Sequence[tuple[str, str]]) -> str:
    column_sql = ",\n    ".join(f"{_quote_identifier(name)} {column_type}" for name, column_type in columns)
    return f"CREATE TABLE IF NOT EXISTS {_quote_identifier(table_name)} (\n    {column_sql}\n);"


def _merged_schema_columns(table_columns: Sequence[tuple[str, str]]) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, column_type in list(table_columns) + _common_columns():
        if name in seen:
            continue
        seen.add(name)
        merged.append((name, column_type))
    return merged


class LocalStorageEngine:
    def __init__(self, database_path: str | Path, *, backend: str = "sqlite", auto_initialize: bool = True) -> None:
        backend_name = str(backend or "").strip().lower()
        if backend_name not in SUPPORTED_LOCAL_STORAGE_BACKENDS:
            raise ValueError(f"Unsupported backend: {backend!r}")
        if backend_name == "duckdb" and not backend_available("duckdb"):
            raise RuntimeError("duckdb backend requested but the duckdb package is not installed")
        self.backend = backend_name
        self.path = Path(database_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | Any | None = None
        if auto_initialize:
            self.ensure_schema()

    @property
    def connection(self) -> sqlite3.Connection | Any:
        if self._conn is None:
            if self.backend == "sqlite":
                conn = sqlite3.connect(str(self.path))
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                self._conn = conn
            else:
                self._conn = _duckdb.connect(str(self.path))  # type: ignore[operator]
        return self._conn

    def close(self) -> None:
        if self._conn is None:
            return
        close = getattr(self._conn, "close", None)
        if callable(close):
            close()
        self._conn = None

    def __enter__(self) -> "LocalStorageEngine":
        _ = self.connection
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _commit(self) -> None:
        commit = getattr(self.connection, "commit", None)
        if callable(commit):
            commit()

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> Any:
        parameters = tuple(params or ())
        result = self.connection.execute(sql, parameters)
        if not sql.lstrip().lower().startswith("select"):
            self._commit()
        return result

    def query(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        result = self.execute(sql, params)
        if result is None:
            return []
        description = getattr(result, "description", None) or []
        columns = [str(column[0]) for column in description]
        rows = result.fetchall()
        payload: list[dict[str, Any]] = []
        for row in rows:
            if isinstance(row, Mapping):
                payload.append(dict(row))
            else:
                payload.append({column: value for column, value in zip(columns, row)})
        return payload

    def ensure_schema(self) -> None:
        for table_name, columns in TABLE_DEFINITIONS.items():
            merged_columns = _merged_schema_columns(columns)
            sql = _build_create_table_sql(table_name, merged_columns)
            self.execute(sql)
            existing_columns = set(self.table_columns(table_name))
            for column_name, column_type in merged_columns:
                if column_name in existing_columns:
                    continue
                alter_type = column_type.replace(" PRIMARY KEY", "")
                self.execute(
                    f"ALTER TABLE {_quote_identifier(table_name)} "
                    f"ADD COLUMN {_quote_identifier(column_name)} {alter_type}"
                )

    def table_exists(self, table_name: str) -> bool:
        if self.backend == "sqlite":
            rows = self.query("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", [table_name])
            return bool(rows)
        rows = self.query("SELECT table_name AS name FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = ?", [table_name])
        return bool(rows)

    def list_tables(self) -> list[str]:
        if self.backend == "sqlite":
            rows = self.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [str(row["name"]) for row in rows]
        rows = self.query("SELECT table_name AS name FROM information_schema.tables WHERE table_schema = current_schema() ORDER BY table_name")
        return [str(row["name"]) for row in rows]

    def table_columns(self, table_name: str) -> list[str]:
        if self.backend == "sqlite":
            rows = self.query(f"PRAGMA table_info({_quote_identifier(table_name)})")
            return [str(row["name"]) for row in rows]
        rows = self.query(
            """
            SELECT column_name AS name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = ?
            ORDER BY ordinal_position
            """,
            [table_name],
        )
        return [str(row["name"]) for row in rows]

    def count(self, table_name: str) -> int:
        rows = self.query(f"SELECT COUNT(*) AS count FROM {_quote_identifier(table_name)}")
        if not rows:
            return 0
        return int(rows[0].get("count") or 0)

    def insert(self, table_name: str, row: Mapping[str, Any]) -> None:
        payload = {str(key): _normalize_value(value) for key, value in dict(row).items()}
        if not payload:
            return
        columns = list(payload)
        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(_quote_identifier(column) for column in columns)
        sql = f"INSERT INTO {_quote_identifier(table_name)} ({column_sql}) VALUES ({placeholders})"
        self.execute(sql, [payload[column] for column in columns])

    def insert_many(self, table_name: str, rows: Iterable[Mapping[str, Any]]) -> int:
        count = 0
        for row in rows:
            self.insert(table_name, row)
            count += 1
        return count

    def replace(self, table_name: str, row: Mapping[str, Any], *, key_columns: Sequence[str]) -> None:
        payload = dict(row)
        where_clauses: list[str] = []
        params: list[Any] = []
        for key in key_columns:
            if key not in payload:
                raise KeyError(f"Missing key column {key!r} for replace on {table_name}")
            where_clauses.append(f"{_quote_identifier(key)} = ?")
            params.append(_normalize_value(payload[key]))
        if where_clauses:
            self.execute(f"DELETE FROM {_quote_identifier(table_name)} WHERE {' AND '.join(where_clauses)}", params)
        self.insert(table_name, payload)

    def fetch(
        self,
        table_name: str,
        *,
        where: str | None = None,
        params: Sequence[Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        sql = f"SELECT * FROM {_quote_identifier(table_name)}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += " LIMIT ?"
            parameters = list(params or []) + [max(0, int(limit))]
        else:
            parameters = list(params or [])
        return self.query(sql, parameters)

    def upsert(self, table_name: str, row: Mapping[str, Any], *, key_columns: Sequence[str]) -> None:
        self.replace(table_name, row, key_columns=key_columns)

    def write_parquet_rows(
        self,
        path: str | Path,
        rows: Sequence[Mapping[str, Any]],
        *,
        compression: str = "zstd",
    ) -> dict[str, Any]:
        if not parquet_available():
            raise RuntimeError("pyarrow is required for parquet storage operations")
        output_path = Path(path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_rows, columns, content_digest = _canonicalize_parquet_rows(rows)
        table = _pyarrow.Table.from_pylist(normalized_rows)  # type: ignore[union-attr]
        _pyarrow_parquet.write_table(  # type: ignore[union-attr]
            table,
            str(output_path),
            compression=compression,
            use_dictionary=False,
            write_statistics=True,
            data_page_version="1.0",
        )
        file_bytes = output_path.read_bytes()
        file_checksum = hashlib.sha256(file_bytes).hexdigest()
        return {
            "ok": True,
            "path": str(output_path),
            "row_count": len(normalized_rows),
            "column_count": len(columns),
            "columns": columns,
            "content_digest": content_digest,
            "file_checksum": file_checksum,
            "file_size_bytes": len(file_bytes),
            "compression": compression,
            "schema_version": PARQUET_STORAGE_INTERFACE_VERSION,
        }

    def read_parquet_rows(self, path: str | Path) -> list[dict[str, Any]]:
        if not parquet_available():
            raise RuntimeError("pyarrow is required for parquet storage operations")
        input_path = Path(path).expanduser().resolve()
        if not input_path.exists():
            return []
        table = _pyarrow_parquet.read_table(str(input_path))  # type: ignore[union-attr]
        rows = table.to_pylist()
        return [dict(row) for row in rows]

    def health(self) -> dict[str, Any]:
        tables = {}
        for table_name in self.list_tables():
            try:
                tables[table_name] = self.count(table_name)
            except Exception:
                tables[table_name] = 0
        return {
            "backend": self.backend,
            "database_path": str(self.path),
            "schema_version": LOCAL_STORAGE_SCHEMA_VERSION,
            "table_count": len(tables),
            "tables": tables,
            "available_backends": {
                "sqlite": True,
                "duckdb": backend_available("duckdb"),
            },
            "parquet": {
                "available": parquet_available(),
                "schema_version": PARQUET_STORAGE_INTERFACE_VERSION,
            },
        }


def create_local_storage_engine(
    database_path: str | Path,
    *,
    backend: str = "sqlite",
    auto_initialize: bool = True,
) -> LocalStorageEngine:
    return LocalStorageEngine(database_path, backend=backend, auto_initialize=auto_initialize)


__all__ = [
    "LOCAL_STORAGE_SCHEMA_VERSION",
    "LocalStorageEngine",
    "PARQUET_STORAGE_INTERFACE_VERSION",
    "SUPPORTED_LOCAL_STORAGE_BACKENDS",
    "backend_available",
    "create_local_storage_engine",
    "parquet_available",
]
