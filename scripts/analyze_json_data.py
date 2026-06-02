#!/usr/bin/env python3
"""
Read-only JSON/JSONL audit tool for betting-stock-api.

- Scans selected project folders for .json and .jsonl files.
- Skips secrets-ish paths and large files by default.
- Produces compact reports under reports/json_data_audit/.
- Uses Python standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DEFAULT_SCAN_DIRS = ["data", "automation_scheduler", "docs", "tests"]
DEFAULT_REPORT_DIR = Path("reports") / "json_data_audit"
DEFAULT_MAX_MB = 25

SKIP_PARTS = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    ".mypy_cache",
    ".pytest_cache",
}

SECRET_PAT = re.compile(
    r"(api[_-]?key|secret|token|auth|authorization|cookie|signature|password|bearer|private[_-]?key)",
    re.IGNORECASE,
)

DATE_PAT = re.compile(r"(date|time|timestamp|created|updated|settled|closed|expires|start|end)", re.IGNORECASE)
PROVIDER_PAT = re.compile(r"(provider|source|sportsbook|book|exchange|kalshi|polymarket|sharp|broker|api)", re.IGNORECASE)
MARKET_PAT = re.compile(r"(sport|league|team|player|market|ticker|contract|selection|odds|line|price|spread|total)", re.IGNORECASE)
OUTCOME_PAT = re.compile(r"(outcome|result|winner|settled|final|won|lost|push|void|score)", re.IGNORECASE)
RISK_PAT = re.compile(r"(risk|safety|dry_run|execution|provider_write|approval|confidence|edge|stake|bet|trade|order)", re.IGNORECASE)
ID_PAT = re.compile(r"(^id$|_id$|uuid|ticker|contract_id|market_id|event_id|game_id|decision_id|run_id)", re.IGNORECASE)

LIKELY_TYPES = [
    ("review_queue", ["review", "queue", "decision", "execution_allowed", "recommended_action"]),
    ("paper_ledger", ["paper", "ledger", "paper_decision", "suggested_stake", "decision_id"]),
    ("outcomes", ["outcome", "settled", "final_outcome", "result", "winner"]),
    ("calibration", ["calibration", "coverage_rate", "matched_outcomes", "brier", "settled_count"]),
    ("collector_report", ["collector", "watchlist", "recheck", "eligible_contracts", "outcomes_persisted"]),
    ("provider_snapshot", ["provider", "snapshot", "received", "valid", "rejected", "raw_payload"]),
    ("test_fixture", ["fixture", "expected", "assert", "test"]),
    ("config", ["enabled", "settings", "config", "threshold", "policy"]),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def path_is_skipped(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return any(part.lower() in SKIP_PARTS for part in parts)


def redact_value(key: str, value: Any) -> Any:
    if SECRET_PAT.search(str(key)):
        return "<REDACTED>"
    if isinstance(value, dict):
        return {k: redact_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(key, v) for v in value[:20]]
    return value


def load_json_file(path: Path) -> Tuple[str, Any, List[str]]:
    errors: List[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except Exception as e:
            return "invalid", None, [f"read_error: {e}"]
    except Exception as e:
        return "invalid", None, [f"read_error: {e}"]

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows = []
        for i, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:
                errors.append(f"line_{i}: {e}")
        if errors and not rows:
            return "invalid_jsonl", None, errors[:10]
        return "jsonl", rows, errors[:10]

    try:
        return "json", json.loads(text), []
    except Exception as e:
        return "invalid", None, [str(e)]


def iter_records(data: Any) -> List[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "records", "data", "results", "markets", "decisions", "outcomes"):
            val = data.get(key)
            if isinstance(val, list):
                return val
        return [data]
    return []


def flatten_keys(obj: Any, prefix: str = "", depth: int = 0, max_depth: int = 3) -> Counter:
    keys: Counter = Counter()
    if depth > max_depth:
        return keys
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            keys[key] += 1
            if isinstance(v, (dict, list)):
                keys.update(flatten_keys(v, key, depth + 1, max_depth))
    elif isinstance(obj, list):
        for item in obj[:25]:
            keys.update(flatten_keys(item, prefix, depth + 1, max_depth))
    return keys


def top_level_keys(data: Any) -> List[str]:
    if isinstance(data, dict):
        return sorted(map(str, data.keys()))[:100]
    if isinstance(data, list) and data and isinstance(data[0], dict):
        c: Counter = Counter()
        for row in data[:200]:
            if isinstance(row, dict):
                c.update(map(str, row.keys()))
        return [k for k, _ in c.most_common(100)]
    return []


def missing_null_counts(records: List[Any]) -> Dict[str, int]:
    counts: Counter = Counter()
    for row in records[:5000]:
        if not isinstance(row, dict):
            continue
        for k, v in row.items():
            if v is None or v == "":
                counts[str(k)] += 1
    return dict(counts.most_common(100))


def schema_drift(records: List[Any]) -> Dict[str, Any]:
    dicts = [r for r in records if isinstance(r, dict)]
    if not dicts:
        return {"has_drift": False, "schema_count": 0, "common_keys": [], "variable_keys": []}
    sigs: Counter = Counter(tuple(sorted(map(str, r.keys()))) for r in dicts[:5000])
    key_counts: Counter = Counter()
    for r in dicts[:5000]:
        key_counts.update(map(str, r.keys()))
    n = len(dicts[:5000])
    common = sorted([k for k, c in key_counts.items() if c == n])[:100]
    variable = sorted([k for k, c in key_counts.items() if c != n])[:100]
    return {
        "has_drift": len(sigs) > 1,
        "schema_count": len(sigs),
        "most_common_schema_size": len(sigs.most_common(1)[0][0]) if sigs else 0,
        "common_keys": common,
        "variable_keys": variable,
    }


def matched_keys(keys: Iterable[str], pat: re.Pattern) -> List[str]:
    return sorted({k for k in keys if pat.search(k)})[:100]


def find_duplicate_ids(records: List[Any]) -> Dict[str, Any]:
    possible_keys: Counter = Counter()
    dicts = [r for r in records if isinstance(r, dict)]
    for r in dicts[:1000]:
        for k in r.keys():
            if ID_PAT.search(str(k)):
                possible_keys[str(k)] += 1
    out = {}
    for k, _ in possible_keys.most_common(20):
        vals = []
        for r in dicts[:10000]:
            val = r.get(k)
            if isinstance(val, (str, int, float)) and str(val):
                vals.append(str(val))
        c = Counter(vals)
        dups = {v: n for v, n in c.items() if n > 1}
        if dups:
            out[k] = {
                "duplicate_value_count": len(dups),
                "examples": dict(list(dups.items())[:25]),
            }
    return out


def likely_record_type(path: str, keys: Iterable[str]) -> str:
    hay = " ".join([path] + list(keys)).lower()
    best_type = "unknown"
    best_score = 0
    for name, terms in LIKELY_TYPES:
        score = sum(1 for t in terms if t in hay)
        if score > best_score:
            best_score = score
            best_type = name
    return best_type


def audit_file(path: Path, root: Path, max_bytes: int) -> Dict[str, Any]:
    rel = safe_rel(path, root)
    size = path.stat().st_size
    base = {
        "path": rel,
        "size_bytes": size,
        "size_mb": round(size / (1024 * 1024), 3),
    }
    if size > max_bytes:
        base.update({
            "json_type": "skipped_large_file",
            "record_count": None,
            "errors": [f"larger_than_limit_{max_bytes}_bytes"],
        })
        return base

    kind, data, errors = load_json_file(path)
    if data is None:
        base.update({
            "json_type": kind,
            "record_count": 0,
            "errors": errors,
            "likely_record_type": "invalid",
        })
        return base

    records = iter_records(data)
    all_keys_counter = flatten_keys(data, max_depth=3)
    all_keys = list(all_keys_counter.keys())
    tkeys = top_level_keys(data)

    base.update({
        "json_type": "jsonl" if kind == "jsonl" else type(data).__name__,
        "record_count": len(records),
        "top_level_keys": tkeys,
        "nested_keys_depth_3": [k for k, _ in all_keys_counter.most_common(150)],
        "missing_null_field_counts": missing_null_counts(records),
        "likely_record_type": likely_record_type(rel, all_keys + tkeys),
        "date_time_fields": matched_keys(all_keys, DATE_PAT),
        "provider_fields": matched_keys(all_keys, PROVIDER_PAT),
        "market_sport_fields": matched_keys(all_keys, MARKET_PAT),
        "outcome_fields": matched_keys(all_keys, OUTCOME_PAT),
        "risk_safety_fields": matched_keys(all_keys, RISK_PAT),
        "duplicate_ids": find_duplicate_ids(records),
        "schema_drift": schema_drift(records),
        "errors": errors,
    })
    return base


def summarize(audits: List[Dict[str, Any]]) -> Dict[str, Any]:
    types = Counter(a.get("likely_record_type", "unknown") for a in audits)
    json_types = Counter(a.get("json_type", "unknown") for a in audits)
    issues = []
    for a in audits:
        path = a["path"]
        if a.get("errors"):
            issues.append({"path": path, "severity": "medium", "issue": "load_or_parse_errors", "details": a.get("errors")})
        drift = a.get("schema_drift") or {}
        if drift.get("has_drift"):
            issues.append({"path": path, "severity": "low", "issue": "schema_drift", "details": drift})
        if a.get("duplicate_ids"):
            issues.append({"path": path, "severity": "medium", "issue": "duplicate_ids", "details": a.get("duplicate_ids")})
        if a.get("json_type") == "skipped_large_file":
            issues.append({"path": path, "severity": "low", "issue": "large_file_skipped", "details": a.get("errors")})

    calibration_files = [a for a in audits if a.get("likely_record_type") in {"outcomes", "paper_ledger", "calibration", "review_queue"}]
    outcome_ready = [a for a in audits if a.get("outcome_fields")]
    market_ready = [a for a in audits if a.get("market_sport_fields")]

    return {
        "generated_at": utc_now(),
        "file_count": len(audits),
        "json_type_counts": dict(json_types),
        "likely_record_type_counts": dict(types),
        "issue_count": len(issues),
        "files_with_outcome_fields": len(outcome_ready),
        "files_with_market_sport_fields": len(market_ready),
        "calibration_related_file_count": len(calibration_files),
        "issues": issues,
    }


def write_reports(report_dir: Path, audits: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)

    inventory = {a["path"]: a for a in audits}
    issues = summary["issues"]
    schema_inventory = {
        a["path"]: {
            "likely_record_type": a.get("likely_record_type"),
            "json_type": a.get("json_type"),
            "record_count": a.get("record_count"),
            "top_level_keys": a.get("top_level_keys", []),
            "nested_keys_depth_3": a.get("nested_keys_depth_3", []),
            "schema_drift": a.get("schema_drift", {}),
        }
        for a in audits
    }

    (report_dir / "latest_summary.json").write_text(
        json.dumps({"summary": summary, "files": inventory}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (report_dir / "schema_inventory.json").write_text(
        json.dumps(schema_inventory, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (report_dir / "issues.json").write_text(
        json.dumps(issues, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    lines = []
    lines.append("# JSON Data Audit")
    lines.append("")
    lines.append(f"Generated: `{summary['generated_at']}`")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Files scanned: **{summary['file_count']}**")
    lines.append(f"- Issues found: **{summary['issue_count']}**")
    lines.append(f"- Calibration-related files: **{summary['calibration_related_file_count']}**")
    lines.append(f"- Files with outcome fields: **{summary['files_with_outcome_fields']}**")
    lines.append(f"- Files with market/sport fields: **{summary['files_with_market_sport_fields']}**")
    lines.append("")
    lines.append("## Likely record type counts")
    lines.append("")
    for k, v in sorted(summary["likely_record_type_counts"].items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## JSON type counts")
    lines.append("")
    for k, v in sorted(summary["json_type_counts"].items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## Data quality issues")
    lines.append("")
    if issues:
        for issue in issues[:100]:
            lines.append(f"- **{issue['severity']}** `{issue['path']}` — {issue['issue']}")
    else:
        lines.append("- No major issues detected by this read-only audit.")
    lines.append("")
    lines.append("## File inventory")
    lines.append("")
    lines.append("| File | Type | Likely record type | Records | Size MB | Drift | Duplicates |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for a in sorted(audits, key=lambda x: x["path"]):
        drift = "yes" if (a.get("schema_drift") or {}).get("has_drift") else "no"
        dups = "yes" if a.get("duplicate_ids") else "no"
        lines.append(
            f"| `{a['path']}` | `{a.get('json_type')}` | `{a.get('likely_record_type')}` | "
            f"{a.get('record_count')} | {a.get('size_mb')} | {drift} | {dups} |"
        )
    lines.append("")
    lines.append("## Most important missing/null fields")
    lines.append("")
    shown = 0
    for a in audits:
        counts = a.get("missing_null_field_counts") or {}
        if counts:
            lines.append(f"### `{a['path']}`")
            for k, v in list(counts.items())[:20]:
                lines.append(f"- `{k}`: {v}")
            lines.append("")
            shown += 1
            if shown >= 20:
                break
    if shown == 0:
        lines.append("- No repeated null/blank top-level fields detected in scanned records.")
        lines.append("")
    lines.append("## Calibration/outcome readiness")
    lines.append("")
    lines.append("Files that appear useful for calibration are those with paper decisions, market identifiers, probabilities, and final outcomes/settlements.")
    lines.append("")
    for a in audits:
        if a.get("likely_record_type") in {"outcomes", "paper_ledger", "calibration", "review_queue"} or a.get("outcome_fields"):
            lines.append(f"- `{a['path']}`: `{a.get('likely_record_type')}`, records={a.get('record_count')}, outcome_fields={len(a.get('outcome_fields') or [])}, market_fields={len(a.get('market_sport_fields') or [])}")
    lines.append("")
    lines.append("## Recommended next cleanup steps")
    lines.append("")
    lines.append("1. Standardize IDs used to join paper decisions to outcomes: ticker/contract_id/market_id/event_id/run_id.")
    lines.append("2. Keep outcome records compact and explicit: final_outcome, outcome_status, settled_at, source, ticker/contract_id.")
    lines.append("3. Separate test fixtures from live/persistent calibration files.")
    lines.append("4. Fix high-value schema drift only after confirming the drift is not intentional versioning.")
    lines.append("5. Never persist raw provider payloads, auth headers, tokens, signatures, or secret-like fields.")
    lines.append("")
    (report_dir / "latest_summary.md").write_text("\n".join(lines), encoding="utf-8")


def discover_files(root: Path, scan_dirs: List[str]) -> List[Path]:
    files: List[Path] = []
    for d in scan_dirs:
        base = root / d
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path_is_skipped(path):
                continue
            if path.suffix.lower() in {".json", ".jsonl"}:
                files.append(path)
    return sorted(set(files))


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of project JSON/JSONL files.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory.")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Report output directory.")
    parser.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB, help="Max file size to fully parse.")
    parser.add_argument("--scan-dir", action="append", help="Directory to scan. Repeatable. Defaults to data, automation_scheduler, docs, tests.")
    parser.add_argument("--dry-run", action="store_true", help="List files that would be scanned, but do not write reports.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    scan_dirs = args.scan_dir or DEFAULT_SCAN_DIRS
    max_bytes = int(args.max_mb * 1024 * 1024)
    files = discover_files(root, scan_dirs)

    if args.dry_run:
        print(f"Project root: {root}")
        print(f"Files found: {len(files)}")
        for f in files[:500]:
            print(safe_rel(f, root))
        if len(files) > 500:
            print(f"... {len(files) - 500} more")
        return 0

    audits = [audit_file(path, root, max_bytes) for path in files]
    summary = summarize(audits)
    report_dir = (root / args.report_dir).resolve()
    write_reports(report_dir, audits, summary)

    print("JSON data audit complete.")
    print(f"Files scanned: {summary['file_count']}")
    print(f"Issues found: {summary['issue_count']}")
    print(f"Report: {report_dir / 'latest_summary.md'}")
    print(f"JSON:   {report_dir / 'latest_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
