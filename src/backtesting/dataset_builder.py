from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .leakage import detect_future_timestamps


PAPER_ONLY_FIXTURE_REQUIRED_FIELDS: tuple[str, ...] = (
    "fixture_id",
    "sport_or_market",
    "event_id",
    "prediction_target",
    "selection",
    "model_probability",
    "market_odds_american",
    "implied_probability",
    "expected_value",
    "stake_units",
    "bankroll_snapshot",
    "result_label",
    "outcome_known",
    "source_type",
    "execution_mode",
)

PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "rows_tested",
    "rows_valid",
    "rows_invalid",
    "missing_field_reasons",
    "warning_reasons",
)

_CORE_DATASET_FIELDS: tuple[str, ...] = (
    "event_id",
    "market_type",
    "recommended_odds",
    "model_probability",
)


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "as_dict"):
        return dict(value.as_dict())
    raise TypeError("rows must be mapping-like")


def _artifact_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)]
    if isinstance(payload, Mapping):
        for key in ("paper_decisions", "rows", "items", "records"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, Mapping)]
        return [dict(payload)]
    return []


def _normalize_row(row: Mapping[str, Any], *, source_path: str) -> dict[str, Any]:
    payload = dict(row)
    normalized = dict(payload)
    normalized["event_id"] = payload.get("event_id") or payload.get("event") or payload.get("event_key")
    normalized["market_type"] = payload.get("market_type") or payload.get("market") or payload.get("market_name")
    normalized["recommended_odds"] = payload.get("recommended_odds")
    if normalized["recommended_odds"] is None:
        normalized["recommended_odds"] = payload.get("odds")
    if normalized["recommended_odds"] is None:
        normalized["recommended_odds"] = payload.get("american_odds")
    normalized["model_probability"] = payload.get("model_probability")
    if normalized["model_probability"] is None:
        normalized["model_probability"] = payload.get("predicted_probability")
    if normalized["model_probability"] is None:
        normalized["model_probability"] = payload.get("probability")
    normalized["edge"] = payload.get("edge")
    if normalized["edge"] is None:
        normalized["edge"] = payload.get("ev_percent")
    if normalized["edge"] is None:
        normalized["edge"] = payload.get("expected_value")
    normalized["stake"] = payload.get("stake")
    if normalized["stake"] is None:
        normalized["stake"] = payload.get("paper_stake")
    if normalized["stake"] is None:
        normalized["stake"] = payload.get("stake_units")
    normalized["closing_line"] = payload.get("closing_line")
    if normalized["closing_line"] is None:
        normalized["closing_line"] = payload.get("closing_odds")
    normalized["timestamp"] = payload.get("timestamp") or payload.get("decision_time") or payload.get("event_time")
    normalized["_source_row_path"] = source_path
    return normalized


def extract_backtest_rows_from_artifact(artifact_path: str | Path) -> dict[str, Any]:
    path = Path(artifact_path)
    if not path.exists():
        return {"ok": False, "status": "missing", "rows": [], "row_count": 0, "warnings": [f"missing:{path}"]}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "status": "invalid_json", "rows": [], "row_count": 0, "warnings": [str(exc)]}
    rows = _artifact_rows(payload)
    if isinstance(payload, Mapping) and any(key in payload for key in ("paper_decisions", "rows", "items", "records")):
        source_path = "root"
        for key in ("paper_decisions", "rows", "items", "records"):
            if isinstance(payload.get(key), list):
                source_path = f"root.{key}"
                break
    else:
        source_path = "root"
    normalized = [_normalize_row(row, source_path=source_path) for row in rows]
    return {
        "ok": True,
        "status": "extracted",
        "artifact_path": str(path),
        "rows": normalized,
        "row_count": len(normalized),
        "warnings": [],
    }


def discover_backtest_artifacts(*, base_dir: str | Path | None = None) -> list[Path]:
    root = Path(base_dir) if base_dir is not None else Path.cwd()
    if not root.exists():
        return []
    candidates: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if path.suffix.lower() not in {".json", ".jsonl", ".ndjson", ".csv"}:
            continue
        if "paper_ledger" in {part.lower() for part in path.parts} or name.startswith("paper") or name.startswith("latest"):
            candidates.append(path)
    return sorted(set(candidates))


def validate_paper_only_fixture_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    row_list = [dict(row) for row in rows if isinstance(row, Mapping)]
    missing_field_reasons: list[dict[str, Any]] = []
    valid_rows = 0
    for index, row in enumerate(row_list):
        missing = [field for field in PAPER_ONLY_FIXTURE_REQUIRED_FIELDS if row.get(field) in (None, "")]
        if missing:
            missing_field_reasons.append({"index": index, "missing_fields": missing})
            continue
        valid_rows += 1
    invalid_rows = len(row_list) - valid_rows
    warnings = []
    if invalid_rows:
        warnings.append("rows_missing_required_fields")
    return {
        "ok": not missing_field_reasons,
        "status": "accepted" if not missing_field_reasons else "rejected",
        "row_count": len(row_list),
        "rows_tested": len(row_list),
        "rows_valid": valid_rows,
        "rows_invalid": invalid_rows,
        "missing_field_reasons": missing_field_reasons,
        "warning_reasons": warnings,
    }


def _field_coverage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    coverage: dict[str, dict[str, int]] = {}
    for field in sorted({key for row in rows for key in row.keys()}):
        present = sum(1 for row in rows if row.get(field) not in (None, ""))
        coverage[field] = {"present": present, "missing": len(rows) - present}
    sport_counts = Counter(str(row.get("sport") or "UNKNOWN") for row in rows)
    return {
        "coverage": coverage,
        "sport_counts": dict(sport_counts),
        "row_count": len(rows),
    }


def build_canonical_backtest_dataset(
    *,
    artifact_paths: Sequence[str | Path],
    output_jsonl_path: str | Path,
    schema_report_path: str | Path,
    require_core_fields: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    dropped = 0
    for artifact_path in artifact_paths:
        extracted = extract_backtest_rows_from_artifact(artifact_path)
        for row in extracted["rows"]:
            normalized = dict(row)
            missing_core = [field for field in _CORE_DATASET_FIELDS if normalized.get(field) in (None, "")]
            if require_core_fields and missing_core:
                dropped += 1
                continue
            rows.append(normalized)

    output_path = Path(output_jsonl_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")

    report: dict[str, Any] = {
        "ok": True,
        "status": "canonical_dataset_built",
        "artifact_count": len(artifact_paths),
        "rows_written": len(rows),
        "rows_dropped": dropped,
        "output_jsonl_path": str(output_path),
        "schema_report_path": str(schema_report_path),
        "rows": rows,
        "field_coverage": _field_coverage(rows),
        "leakage_summary": detect_future_timestamps(rows),
    }
    schema_path = Path(schema_report_path)
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(json.dumps(report["field_coverage"], indent=2, sort_keys=True), encoding="utf-8")
    return report


def load_canonical_backtest_dataset(path: str | Path) -> list[dict[str, Any]]:
    dataset_path = Path(path)
    if not dataset_path.exists():
        return []
    if dataset_path.suffix.lower() in {".json", ".jsonl", ".ndjson"}:
        text = dataset_path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        if dataset_path.suffix.lower() == ".json":
            payload = json.loads(text)
            return [row for row in payload if isinstance(row, Mapping)] if isinstance(payload, list) else ([dict(payload)] if isinstance(payload, Mapping) else [])
        rows: list[dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, Mapping):
                rows.append(dict(payload))
        return rows
    if dataset_path.suffix.lower() == ".csv":
        import csv

        with dataset_path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    return [{"value": line} for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_canonical_dataset_report(report: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(report)
    payload.pop("rows", None)
    payload.pop("schema_report_path", None)
    payload["field_coverage"] = dict(report.get("field_coverage", {}))
    return payload


__all__ = [
    "PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS",
    "PAPER_ONLY_FIXTURE_REQUIRED_FIELDS",
    "build_canonical_backtest_dataset",
    "discover_backtest_artifacts",
    "extract_backtest_rows_from_artifact",
    "load_canonical_backtest_dataset",
    "summarize_canonical_dataset_report",
    "validate_paper_only_fixture_rows",
]
