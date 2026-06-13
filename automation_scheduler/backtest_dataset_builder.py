"""Canonical historical backtest dataset builder.

This module does not run backtests.

It builds clean normalized dataset rows that can feed:
automation_scheduler.backtesting_engine.run_backtest
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import json

from .backtest_leakage import evaluate_backtest_rows_leakage, summarize_backtest_leakage_report
from .backtest_schema import (
    REQUIRED_BACKTEST_FIELDS,
    describe_backtest_schema,
    missing_required_backtest_fields,
    normalize_backtest_row,
)


DEFAULT_CANDIDATE_ARTIFACTS: tuple[str, ...] = (
    "data/paper_ledger/latest.json",
    "data/paper_ledger/paper_decisions.json",
    "data/review_queue/latest.json",
    "data/review_queue/review_queue.json",
)


DEFAULT_CANDIDATE_DIRS: tuple[str, ...] = (
    "data/paper_ledger/items",
    "data/review_queue/items",
    "data/reports",
    "data/backtests",
    "data/clv",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _find_row_lists(obj: Any, prefix: str = "root") -> list[tuple[str, list[dict[str, Any]]]]:
    found: list[tuple[str, list[dict[str, Any]]]] = []

    if isinstance(obj, list):
        dict_rows = [row for row in obj if isinstance(row, dict)]
        if dict_rows:
            found.append((prefix, dict_rows))
        return found

    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{prefix}.{key}"
            if isinstance(value, list):
                dict_rows = [row for row in value if isinstance(row, dict)]
                if dict_rows:
                    found.append((child, dict_rows))
            elif isinstance(value, dict):
                found.extend(_find_row_lists(value, child))

    return found


def discover_backtest_artifacts(
    *,
    base_dir: str | Path = ".",
    candidate_files: tuple[str, ...] = DEFAULT_CANDIDATE_ARTIFACTS,
    candidate_dirs: tuple[str, ...] = DEFAULT_CANDIDATE_DIRS,
    max_files_per_dir: int = 25,
) -> list[Path]:
    """Discover likely row-based historical/paper artifacts."""

    root = Path(base_dir)
    artifacts: list[Path] = []

    for item in candidate_files:
        path = root / item
        if path.exists() and path.is_file():
            artifacts.append(path)

    for item in candidate_dirs:
        folder = root / item
        if not folder.exists() or not folder.is_dir():
            continue

        artifacts.extend(
            sorted(
                folder.glob("*.json"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )[:max_files_per_dir]
        )

    seen: set[str] = set()
    deduped: list[Path] = []
    for path in artifacts:
        key = str(path.resolve())
        if key not in seen:
            seen.add(key)
            deduped.append(path)

    return deduped


def extract_backtest_rows_from_artifact(path: str | Path) -> dict[str, Any]:
    """Extract and normalize candidate rows from one artifact."""

    artifact_path = Path(path)
    payload = _load_json(artifact_path)
    row_lists = _find_row_lists(payload)

    rows: list[dict[str, Any]] = []
    row_sources: list[dict[str, Any]] = []

    for row_path, found_rows in row_lists:
        for index, row in enumerate(found_rows):
            normalized = normalize_backtest_row(row)
            normalized["_source_artifact"] = str(artifact_path)
            normalized["_source_row_path"] = row_path
            normalized["_source_row_index"] = index
            rows.append(normalized)
            row_sources.append(
                {
                    "artifact": str(artifact_path),
                    "row_path": row_path,
                    "row_index": index,
                }
            )

    return {
        "artifact": str(artifact_path),
        "row_list_count": len(row_lists),
        "row_count": len(rows),
        "rows": rows,
        "row_sources": row_sources,
    }



def summarize_dataset_field_coverage(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    fields = [
        "sport",
        "league",
        "market",
        "event_id",
        "odds_at_decision_time",
        "model_probability",
        "features_known_at_decision_time",
        "final_result",
        "profit_loss",
        "closing_line",
        "clv",
    ]

    coverage: dict[str, dict[str, Any]] = {}
    for field in fields:
        present = sum(1 for row in rows if row.get(field) not in (None, ""))
        coverage[field] = {
            "present": present,
            "missing": total - present,
            "coverage_percent": round((present / total) * 100, 4) if total else 0.0,
        }

    sport_counts: dict[str, int] = {}
    league_counts: dict[str, int] = {}
    for row in rows:
        sport = row.get("sport") or "UNKNOWN"
        league = row.get("league") or "UNKNOWN"
        sport_counts[str(sport)] = sport_counts.get(str(sport), 0) + 1
        league_counts[str(league)] = league_counts.get(str(league), 0) + 1

    return {
        "row_count": total,
        "coverage": coverage,
        "sport_counts": dict(sorted(sport_counts.items(), key=lambda item: (-item[1], item[0]))[:50]),
        "league_counts": dict(sorted(league_counts.items(), key=lambda item: (-item[1], item[0]))[:50]),
    }


def build_canonical_backtest_dataset(
    *,
    artifact_paths: list[str | Path] | tuple[str | Path, ...] | None = None,
    base_dir: str | Path = ".",
    output_jsonl_path: str | Path = "data/backtests/canonical/latest.jsonl",
    schema_report_path: str | Path = "data/backtests/canonical/schema_report.json",
    require_core_fields: bool = False,
) -> dict[str, Any]:
    """Build a canonical normalized JSONL dataset and schema report.

    `require_core_fields=False` is intentional for early paper operations:
    incomplete rows are retained but reported. This lets us learn coverage gaps
    without throwing away useful rows too early.
    """

    if artifact_paths is None:
        artifacts = discover_backtest_artifacts(base_dir=base_dir)
    else:
        artifacts = [Path(path) for path in artifact_paths]

    all_rows: list[dict[str, Any]] = []
    artifact_summaries: list[dict[str, Any]] = []

    for artifact in artifacts:
        if not artifact.exists():
            artifact_summaries.append(
                {
                    "artifact": str(artifact),
                    "exists": False,
                    "row_count": 0,
                    "row_list_count": 0,
                }
            )
            continue

        try:
            extracted = extract_backtest_rows_from_artifact(artifact)
        except Exception as exc:
            artifact_summaries.append(
                {
                    "artifact": str(artifact),
                    "exists": True,
                    "error": str(exc),
                    "row_count": 0,
                    "row_list_count": 0,
                }
            )
            continue

        rows = extracted["rows"]
        all_rows.extend(rows)
        artifact_summaries.append(
            {
                "artifact": extracted["artifact"],
                "exists": True,
                "row_count": extracted["row_count"],
                "row_list_count": extracted["row_list_count"],
            }
        )

    filtered_rows: list[dict[str, Any]] = []
    dropped_rows: list[dict[str, Any]] = []
    missing_counts: dict[str, int] = {}

    for index, row in enumerate(all_rows):
        missing = missing_required_backtest_fields(row)
        for field in missing:
            missing_counts[field] = missing_counts.get(field, 0) + 1

        core_missing = [
            field
            for field in (
                "event_id",
                "market",
                "odds_at_decision_time",
                "model_probability",
            )
            if field in missing
        ]

        if require_core_fields and core_missing:
            dropped_rows.append(
                {
                    "index": index,
                    "source_artifact": row.get("_source_artifact"),
                    "core_missing": core_missing,
                }
            )
            continue

        filtered_rows.append(row)

    leakage_report = evaluate_backtest_rows_leakage(filtered_rows)
    leakage_summary = summarize_backtest_leakage_report(leakage_report)

    output_path = Path(output_jsonl_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in filtered_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    schema_report = {
        "ok": True,
        "policy": "canonical_historical_backtest_dataset",
        "schema": describe_backtest_schema(),
        "artifacts_seen": len(artifacts),
        "artifact_summaries": artifact_summaries,
        "raw_rows_found": len(all_rows),
        "rows_written": len(filtered_rows),
        "rows_dropped": len(dropped_rows),
        "dropped_rows": dropped_rows[:200],
        "required_fields": list(REQUIRED_BACKTEST_FIELDS),
        "missing_required_field_counts": dict(sorted(missing_counts.items())),
        "field_coverage": summarize_dataset_field_coverage(filtered_rows),
        "leakage_summary": leakage_summary,
        "output_jsonl_path": str(output_path),
        "schema_report_path": str(schema_report_path),
    }

    _write_json(Path(schema_report_path), schema_report)

    return schema_report


def load_canonical_backtest_dataset(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    dataset_path = Path(path)

    if not dataset_path.exists():
        return rows

    for line in dataset_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        rows.append(json.loads(stripped))

    return rows


def summarize_canonical_dataset_report(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(report.get("ok")),
        "policy": report.get("policy"),
        "artifacts_seen": report.get("artifacts_seen", 0),
        "raw_rows_found": report.get("raw_rows_found", 0),
        "rows_written": report.get("rows_written", 0),
        "rows_dropped": report.get("rows_dropped", 0),
        "missing_required_field_counts": dict(report.get("missing_required_field_counts", {})),
        "field_coverage": dict(report.get("field_coverage", {})),
        "leakage_summary": dict(report.get("leakage_summary", {})),
        "output_jsonl_path": report.get("output_jsonl_path"),
        "schema_report_path": report.get("schema_report_path"),
    }
