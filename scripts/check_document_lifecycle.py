from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DOC_ROOT = ROOT / "docs"
RETENTION_INDEX_PATH = DOC_ROOT / "DOCUMENT_RETENTION_INDEX.md"
MASTER_INDEX_PATH = DOC_ROOT / "MASTER_DOCUMENT_INDEX.md"
ALLOWED_DOC_ROOT_MARKDOWN = {
    "DOCUMENT_RETENTION_INDEX.md",
    "BUSINESS_STRATEGY.md",
    "INTELLECTUAL_PROPERTY_REGISTER.md",
    "MASTER_DOCUMENT_INDEX.md",
    "MASTER_ROADMAP.md",
    "NEXT_ACTION.md",
    "PRODUCT_SPEC.md",
    "PROJECT_STATUS.md",
    "STATUS_UPDATE_POLICY.md",
}
SEARCHABLE_TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".yml",
    ".yaml",
    ".ps1",
    ".psm1",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".bat",
    ".cmd",
}
SEARCH_EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "build",
    "dist",
}


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _tracked_document_files(root: Path = ROOT) -> list[Path]:
    docs_root = root / "docs"
    if not docs_root.exists():
        return []
    files = [
        path.resolve()
        for path in docs_root.rglob("*")
        if path.is_file() and path.suffix.lower() in SEARCHABLE_TEXT_EXTENSIONS
    ]
    return sorted({path for path in files}, key=lambda item: _relative(item).lower())


def _title(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return path.stem.replace("_", " ").replace("-", " ").title()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem.replace("_", " ").replace("-", " ").title()
    return path.stem.replace("_", " ").replace("-", " ").title()


def _category(path: Path) -> str:
    rel = _relative(path)
    if rel == "docs/MASTER_ROADMAP.md":
        return "ARCHITECTURE DOCUMENT"
    if rel in {"docs/PROJECT_STATUS.md", "docs/NEXT_ACTION.md"}:
        return "ARCHITECTURE DOCUMENT"
    if rel == "docs/STATUS_UPDATE_POLICY.md":
        return "STANDARD"
    if rel in {"docs/MASTER_DOCUMENT_INDEX.md", "docs/DOCUMENT_RETENTION_INDEX.md"}:
        return "INDEX"
    if rel.startswith("docs/architecture/adr/"):
        return "DECISION RECORD"
    if rel.startswith("docs/architecture/"):
        return "ARCHITECTURE DOCUMENT"
    if rel.startswith("docs/contracts/"):
        return "CONTRACT"
    if rel.startswith("docs/development/"):
        return "STANDARD"
    if rel.startswith("docs/operations/"):
        return "RUNBOOK"
    if rel.startswith("docs/catalogs/"):
        return "CATALOG"
    if rel.startswith("docs/discovery/"):
        return "DISCOVERY REPORT"
    if rel.startswith("docs/reports/audits/"):
        return "AUDIT REPORT"
    if rel.startswith("docs/reports/checkpoints/"):
        return "CHECKPOINT"
    if rel.startswith("docs/reports/proofs/"):
        return "PROOF"
    if rel.startswith("docs/reports/inventories/"):
        return "INVENTORY"
    if rel.startswith("docs/reports/gap_analysis/"):
        return "GAP ANALYSIS"
    if rel.startswith("docs/reports/matrices/"):
        return "MATRIX"
    if rel.startswith("docs/summaries/"):
        return "SUMMARY"
    if rel.startswith("docs/archive/milestones/"):
        return "MILESTONE SUMMARY"
    if rel.startswith("docs/archive/historical_reports/"):
        return "HISTORICAL REPORT"
    if rel.startswith("docs/archive/deprecated_docs/"):
        return "DEPRECATED DOC"
    if rel.startswith("docs/archive/completed_phases/"):
        return "COMPLETED PHASE DOC"
    return "DOCUMENT"


def _knowledge_classification(category: str) -> str:
    if category in {"ARCHITECTURE DOCUMENT", "CONTRACT", "STANDARD", "RUNBOOK", "INDEX"}:
        return category
    if category == "DECISION RECORD":
        return "DECISION RECORD"
    if category in {"MILESTONE SUMMARY", "SUMMARY", "CATALOG", "MATRIX"}:
        return "SECONDARY KNOWLEDGE"
    if category in {"DISCOVERY REPORT", "CHECKPOINT", "PROOF", "INVENTORY", "GAP ANALYSIS", "AUDIT REPORT"}:
        return "VALIDATION OUTPUT"
    if category in {"HISTORICAL REPORT", "DEPRECATED DOC", "COMPLETED PHASE DOC"}:
        return "HISTORICAL EVIDENCE"
    return "SECONDARY KNOWLEDGE"


def _lifecycle_state(path: Path, category: str) -> str:
    rel = _relative(path)
    name = path.name
    if rel == "docs/MASTER_ROADMAP.md":
        return "ACTIVE"
    if rel in {"docs/PROJECT_STATUS.md", "docs/NEXT_ACTION.md", "docs/STATUS_UPDATE_POLICY.md"}:
        return "ACTIVE"
    if rel in {"docs/MASTER_DOCUMENT_INDEX.md", "docs/DOCUMENT_RETENTION_INDEX.md"}:
        return "ACTIVE"
    if rel.startswith("docs/archive/historical_reports/"):
        return "ARCHIVED"
    if rel.startswith("docs/archive/deprecated_docs/"):
        return "ARCHIVED"
    if rel.startswith("docs/archive/completed_phases/"):
        return "ARCHIVED"
    if rel.startswith("docs/archive/milestones/"):
        return "CONSOLIDATED"
    if rel.startswith("docs/architecture/adr/"):
        return "DECISION CAPTURED"
    if rel.startswith("docs/architecture/"):
        return "ACTIVE"
    if rel.startswith("docs/contracts/"):
        return "ACTIVE"
    if rel.startswith("docs/development/"):
        return "ACTIVE"
    if rel.startswith("docs/operations/"):
        return "ACTIVE"
    if rel.startswith("docs/catalogs/"):
        return "ACTIVE"
    if rel.startswith("docs/reports/matrices/"):
        return "ACTIVE"
    if rel.startswith("docs/reports/gap_analysis/"):
        return "ACTIVE"
    if rel.startswith("docs/reports/audits/"):
        if name in {"AUDIT_RETENTION_REGISTER.md", "MISSING_GOVERNANCE_REPORT.md"}:
            return "ACTIVE"
        return "DECISION CAPTURED"
    if rel.startswith("docs/reports/checkpoints/"):
        if name in {"ACTIVE_RUNTIME_TEST_GATE.md", "QUALITY_GATE_CHECKLIST.md"}:
            return "ACTIVE"
        return "DECISION CAPTURED"
    if rel.startswith("docs/reports/proofs/"):
        return "DECISION CAPTURED"
    if rel.startswith("docs/reports/inventories/"):
        if name.endswith(".json") or name.endswith(".txt"):
            return "WORKING"
        return "WORKING"
    if rel.startswith("docs/discovery/"):
        if name.startswith("COMPLETE_"):
            return "CONSOLIDATED"
        if name.startswith("CURRENT_"):
            return "WORKING"
        return "WORKING"
    if rel.startswith("docs/summaries/"):
        return "CONSOLIDATED"
    return "WORKING"


def _purpose(path: Path, category: str) -> str:
    name = path.name
    if category == "INDEX":
        return "Authoritative document index"
    if category == "ARCHITECTURE DOCUMENT":
        if name == "PROJECT_STATUS.md":
            return "Canonical project status snapshot"
        if name == "NEXT_ACTION.md":
            return "Canonical next action handoff"
        return "Current architecture guidance"
    if category == "CONTRACT":
        return "Canonical contract surface"
    if category == "STANDARD":
        if name == "STATUS_UPDATE_POLICY.md":
            return "Canonical status update policy"
        return "Engineering standard or contributor guidance"
    if category == "RUNBOOK":
        return "Operational runbook or workflow"
    if category == "DECISION RECORD":
        return "Architecture decision record"
    if category == "CATALOG":
        return "Canonical catalog or capability map"
    if category == "MATRIX":
        return "Cross-reference matrix or capability table"
    if category == "SUMMARY":
        return "Historical or executive summary"
    if category == "MILESTONE SUMMARY":
        return "Consolidated milestone summary"
    if category == "HISTORICAL REPORT":
        return "Historical evidence"
    if category == "DEPRECATED DOC":
        return "Deprecated historical documentation"
    if category == "COMPLETED PHASE DOC":
        return "Completed phase evidence"
    if category == "DISCOVERY REPORT":
        return "Discovery report"
    if category == "AUDIT REPORT":
        return "Audit or governance report"
    if category == "CHECKPOINT":
        return "Checkpoint report"
    if category == "PROOF":
        return "Validation proof"
    if category == "INVENTORY":
        return "Inventory snapshot"
    if category == "GAP ANALYSIS":
        return "Gap analysis or readiness report"
    return name.replace("_", " ").replace("-", " ").title()


def _unique_value(category: str, state: str) -> str:
    if state == "ACTIVE":
        return "Current authoritative documentation"
    if state == "DECISION CAPTURED":
        return "Decision captured elsewhere; retained as evidence"
    if state == "CONSOLIDATED":
        return "Milestone summary replacing multiple interim reports"
    if state == "ARCHIVED":
        return "Historical evidence preserved for review"
    if state == "WORKING":
        return "Temporary work product or active discovery artifact"
    return "Documentation artifact"


def _searchable_reference_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SEARCHABLE_TEXT_EXTENSIONS:
            continue
        if set(path.parts) & SEARCH_EXCLUDED_PARTS:
            continue
        files.append(path.resolve())
    return sorted({path for path in files}, key=lambda item: _relative(item).lower())


def _active_reference_buckets(doc_paths: list[Path]) -> dict[str, dict[str, list[str]]]:
    if not doc_paths:
        return {}
    buckets: dict[str, dict[str, list[str]]] = {
        _relative(path): {"active": [], "historical": []} for path in doc_paths
    }
    needles = [_relative(path) for path in doc_paths]
    for referrer in _searchable_reference_files(ROOT):
        try:
            text = referrer.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "docs/" not in text:
            continue
        referrer_rel = _relative(referrer)
        bucket = "historical" if referrer_rel.startswith("docs/archive/") else "active"
        for matched in needles:
            if matched in text and referrer_rel not in buckets[matched][bucket]:
                buckets[matched][bucket].append(referrer_rel)
    for entry in buckets.values():
        entry["active"].sort()
        entry["historical"].sort()
    return buckets


def discover_documents(root: Path = ROOT) -> list[Path]:
    return _tracked_document_files(root)


def _docs_root_markdown_offenders(root: Path = ROOT) -> list[str]:
    offenders = []
    for path in (root / "docs").iterdir():
        if path.is_file() and path.suffix.lower() == ".md" and path.name not in ALLOWED_DOC_ROOT_MARKDOWN:
            offenders.append(_relative(path))
    return sorted(offenders)


def _parse_register(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    entries: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        if line.startswith("| path ") or line.startswith("| ---"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 7:
            continue
        doc_path, title, category, lifecycle_state, referenced_by, unique_value, recommended_action = parts[:7]
        entries[doc_path] = {
            "path": doc_path,
            "title": title,
            "category": category,
            "lifecycle_state": lifecycle_state,
            "referenced_by": referenced_by,
            "unique_value": unique_value,
            "recommended_action": recommended_action,
        }
    return entries


def build_document_records(root: Path = ROOT) -> list[dict[str, Any]]:
    docs = discover_documents(root)
    refs = _active_reference_buckets(docs)
    records: list[dict[str, Any]] = []
    for path in docs:
        rel = _relative(path)
        category = _category(path)
        state = _lifecycle_state(path, category)
        active_refs = refs.get(rel, {}).get("active", [])
        historical_refs = refs.get(rel, {}).get("historical", [])
        if active_refs:
            referenced_by = "; ".join(active_refs[:3])
        elif historical_refs:
            referenced_by = "historical evidence only"
        else:
            referenced_by = "unreferenced"
        if state == "ARCHIVED":
            recommended_action = "KEEP ARCHIVE"
        elif state == "CONSOLIDATED":
            recommended_action = "KEEP ACTIVE"
        elif state == "DECISION CAPTURED" and rel.startswith("docs/reports/"):
            recommended_action = "ARCHIVE"
        elif state == "WORKING" and rel.startswith("docs/discovery/"):
            recommended_action = "ARCHIVE"
        else:
            recommended_action = "KEEP ACTIVE"
        records.append(
            {
                "path": rel,
                "title": _title(path),
                "category": category,
                "knowledge_classification": _knowledge_classification(category),
                "lifecycle_state": state,
                "purpose": _purpose(path, category),
                "referenced_by": referenced_by,
                "unique_value": _unique_value(category, state),
                "recommended_action": recommended_action,
            }
        )
    return records


def _duplicate_name_groups(records: list[dict[str, Any]]) -> list[list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in records:
        grouped[Path(row["path"]).name.lower()].append(row["path"])
    return [sorted(paths) for paths in grouped.values() if len(paths) > 1]


def build_document_retention_index(root: Path = ROOT) -> str:
    records = build_document_records(root)
    counts = Counter(row["lifecycle_state"] for row in records)
    lines = [
        "# Document Retention Index",
        "",
        "This register classifies every tracked document under `docs/` so the repository can keep durable knowledge, archive historical evidence, and identify temporary work products that should eventually be consolidated or deleted.",
        "",
        f"- scanned_files: {len(records)}",
        f"- working: {counts.get('WORKING', 0)}",
        f"- active: {counts.get('ACTIVE', 0)}",
        f"- decision_captured: {counts.get('DECISION CAPTURED', 0)}",
        f"- consolidated: {counts.get('CONSOLIDATED', 0)}",
        f"- archived: {counts.get('ARCHIVED', 0)}",
        f"- delete_candidate: {counts.get('DELETE CANDIDATE', 0)}",
        f"- delete_approved: {counts.get('DELETE APPROVED', 0)}",
        "",
        "| path | title | category | lifecycle state | referenced by | unique value | recommended action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in records:
        lines.append(
            "| {path} | {title} | {category} | {lifecycle_state} | {referenced_by} | {unique_value} | {recommended_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Policy Note",
            "",
            "The register is advisory for archive growth and deletion decisions. Archive-first behavior remains the default when a document still has historical value.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_master_document_index(root: Path = ROOT) -> str:
    records = build_document_records(root)
    active_records = [row for row in records if row["lifecycle_state"] in {"ACTIVE", "DECISION CAPTURED", "CONSOLIDATED"}]
    active_records.sort(key=lambda row: (row["category"], row["path"]))
    archive_records = [row for row in records if row["lifecycle_state"] == "ARCHIVED"]
    archive_records.sort(key=lambda row: row["path"])
    lines = [
        "# Master Document Index",
        "",
        "This index points readers to the current truth and the durable historical entry points.",
        "",
        "## Current Truth",
        "",
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in active_records:
        grouped[row["category"]].append(row)
    for category in sorted(grouped):
        lines.append(f"### {category}")
        for row in grouped[category]:
            lines.append(f"- `{row['path']}` - {row['title']}")
        lines.append("")
    lines.extend(
        [
            "## Historical Entry Points",
            "",
        ]
    )
    for row in archive_records[:40]:
        lines.append(f"- `{row['path']}` - {row['title']}")
    if len(archive_records) > 40:
        lines.append("")
        lines.append(f"_Additional historical entries are listed in `{RETENTION_INDEX_PATH.as_posix()}`._")
    lines.extend(
        [
            "",
            "## Navigation Guidance",
            "",
            "- Start with the architecture front door for system shape.",
            "- Use the contract index for current schema and API truth.",
            "- Use the retention index to understand lifecycle state and archive policy.",
            "- Use archived milestones and historical reports only when tracing how a decision was made.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_document_indexes(root: Path = ROOT) -> tuple[Path, Path]:
    retention = build_document_retention_index(root)
    master = build_master_document_index(root)
    RETENTION_INDEX_PATH.write_text(retention, encoding="utf-8")
    MASTER_INDEX_PATH.write_text(master, encoding="utf-8")
    return RETENTION_INDEX_PATH, MASTER_INDEX_PATH


def collect_document_lifecycle_report(root: Path = ROOT) -> dict[str, Any]:
    records = build_document_records(root)
    register_entries = _parse_register(RETENTION_INDEX_PATH)
    discovered_paths = {row["path"] for row in records}
    register_paths = set(register_entries)
    missing_from_register = sorted(discovered_paths - register_paths)
    register_only = sorted(register_paths - discovered_paths)
    root_markdown_offenders = _docs_root_markdown_offenders(root)
    duplicate_name_groups = _duplicate_name_groups(records)
    active_working = [row["path"] for row in records if row["lifecycle_state"] == "WORKING" and row["recommended_action"] == "ARCHIVE"]
    warnings: list[str] = []
    clear_violations: list[str] = []

    if root_markdown_offenders:
        clear_violations.append("docs_root_markdown_offenders")
    if missing_from_register:
        clear_violations.append(f"missing_register_entries:{len(missing_from_register)}")
    if register_only:
        warnings.append(f"register_only_entries:{len(register_only)}")
    if duplicate_name_groups:
        warnings.append(f"duplicate_document_names:{len(duplicate_name_groups)}")
    if active_working:
        warnings.append(f"working_documents_needing_attention:{len(active_working)}")

    counts = Counter(row["lifecycle_state"] for row in records)
    report = {
        "ok": not clear_violations,
        "status": "ok" if not warnings and not clear_violations else ("advisory" if not clear_violations else "violation"),
        "scanned_count": len(records),
        "register_count": len(register_entries),
        "working_count": counts.get("WORKING", 0),
        "active_count": counts.get("ACTIVE", 0),
        "decision_captured_count": counts.get("DECISION CAPTURED", 0),
        "consolidated_count": counts.get("CONSOLIDATED", 0),
        "archived_count": counts.get("ARCHIVED", 0),
        "delete_candidate_count": counts.get("DELETE CANDIDATE", 0),
        "delete_approved_count": counts.get("DELETE APPROVED", 0),
        "missing_from_register": missing_from_register,
        "register_only": register_only,
        "root_markdown_offenders": root_markdown_offenders,
        "duplicate_name_groups": duplicate_name_groups,
        "working_documents_needing_attention": active_working,
        "warnings": warnings,
        "clear_violations": clear_violations,
        "records": records,
        "register_entries": register_entries,
    }
    return report


def _render_text(report: dict[str, Any]) -> str:
    lines = [
        f"document_lifecycle: {report.get('status')}",
        f"scanned_count: {report.get('scanned_count')}",
        f"register_count: {report.get('register_count')}",
        f"working_count: {report.get('working_count')}",
        f"active_count: {report.get('active_count')}",
        f"decision_captured_count: {report.get('decision_captured_count')}",
        f"consolidated_count: {report.get('consolidated_count')}",
        f"archived_count: {report.get('archived_count')}",
        f"delete_candidate_count: {report.get('delete_candidate_count')}",
        f"delete_approved_count: {report.get('delete_approved_count')}",
        f"missing_from_register: {len(report.get('missing_from_register') or [])}",
        f"register_only: {len(report.get('register_only') or [])}",
        f"root_markdown_offenders: {len(report.get('root_markdown_offenders') or [])}",
        f"duplicate_name_groups: {len(report.get('duplicate_name_groups') or [])}",
        f"working_documents_needing_attention: {len(report.get('working_documents_needing_attention') or [])}",
        f"warnings: {len(report.get('warnings') or [])}",
        f"clear_violations: {len(report.get('clear_violations') or [])}",
    ]
    for item in (report.get("warnings") or [])[:10]:
        lines.append(f"- warning: {item}")
    for item in (report.get("clear_violations") or [])[:10]:
        lines.append(f"- violation: {item}")
    return "\n".join(lines)


def _write_json_report(output: str, report: dict[str, Any]) -> Path:
    path = Path(output)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check document lifecycle governance.")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--write-indexes", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)

    if args.write_indexes:
        write_document_indexes(ROOT)

    report = collect_document_lifecycle_report(ROOT)
    if args.output == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    if args.write_report:
        _write_json_report("docs/reports/inventories/document_lifecycle_report.json", report)
    return 2 if report.get("clear_violations") else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
