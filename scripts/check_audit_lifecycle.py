from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SCAN_DIRS = (
    ROOT / "docs" / "reports" / "audits",
    ROOT / "docs" / "reports" / "checkpoints",
    ROOT / "docs" / "reports" / "proofs",
    ROOT / "docs" / "archive" / "historical_reports",
)
REGISTER_PATH = ROOT / "docs" / "reports" / "audits" / "AUDIT_RETENTION_REGISTER.md"

ACTIVE_REFERENCE_DOCS = (
    ROOT / "docs" / "architecture",
    ROOT / "docs" / "contracts",
    ROOT / "docs" / "development",
    ROOT / "docs" / "operations",
)
ACTIVE_REFERENCE_TESTS = ROOT / "tests"
ACTIVE_REFERENCE_SCRIPTS = ROOT / "scripts"


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _stem_label(path: Path) -> str:
    text = path.stem.replace("_", " ").replace("-", " ").strip()
    if not text:
        return path.stem
    return re.sub(r"\s+", " ", text).title()


def _purpose(path: Path) -> str:
    name = path.name
    if path.parent.as_posix().endswith("archive/historical_reports"):
        return "Historical audit evidence"
    if name == "AUDIT_RETENTION_REGISTER.md":
        return "Lifecycle register for audit, checkpoint, proof, and historical report material"
    if name == "MISSING_GOVERNANCE_REPORT.md":
        return "Open governance gaps and remaining recommendations"
    if name == "CONTRACT_CONSISTENCY_REPORT.md":
        return "Contract alignment and consistency assessment"
    if name == "OPENAPI_DEPENDENCY_AND_RISK_REPORT.md":
        return "OpenAPI dependency and public contract risk assessment"
    if name == "TERMINOLOGY_INVENTORY_AND_CLASSIFICATION.md":
        return "Terminology inventory and classification evidence"
    if name == "VENDOR_REFERENCE_CLASSIFICATION.md":
        return "Vendor wording classification for public documentation"
    if name == "ACTIVE_RUNTIME_TEST_GATE.md":
        return "Current active test-gate boundary"
    if name == "QUALITY_GATE_CHECKLIST.md":
        return "Current quality-gate checklist"
    if name == "ARCHITECTURE_GATE_PROOF.md":
        return "Proof that architecture checks and gates passed"
    if name == "OPENAPI_VALIDATION_PROOF.md":
        return "Proof that OpenAPI validation passed"
    if name == "GITIGNORE_SOURCE_SAFETY_PROOF.md":
        return "Proof that source files are not hidden by ignore rules"
    if name == "PHASE10K8ZGA_PROVIDER_REGISTRY_RUNTIME_BLOCKER_PROOF.md":
        return "Proof of the provider registry runtime blocker investigation"
    return _stem_label(path)


def _decision_captured_where(path: Path, state: str) -> str:
    name = path.name
    if state == "ARCHIVE":
        return "docs/architecture/AUDIT_LIFECYCLE_POLICY.md"
    if name == "AUDIT_RETENTION_REGISTER.md":
        return "docs/architecture/AUDIT_LIFECYCLE_POLICY.md"
    if name == "MISSING_GOVERNANCE_REPORT.md":
        return "docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md; docs/architecture/PRODUCTION_READINESS.md"
    if name == "CONTRACT_CONSISTENCY_REPORT.md":
        return "docs/contracts/CONTRACT_INDEX.md"
    if name == "OPENAPI_DEPENDENCY_AND_RISK_REPORT.md":
        return "docs/architecture/OPENAPI_CONTRACT_GOVERNANCE.md; docs/architecture/VENDOR_NEUTRALITY_AND_OPENAPI_NAMING.md"
    if name == "TERMINOLOGY_INVENTORY_AND_CLASSIFICATION.md":
        return "docs/architecture/TERMINOLOGY_STANDARD.md"
    if name == "VENDOR_REFERENCE_CLASSIFICATION.md":
        return "docs/architecture/VENDOR_NEUTRALITY_AND_OPENAPI_NAMING.md"
    if name == "ACTIVE_RUNTIME_TEST_GATE.md":
        return "docs/operations/VALIDATION_RUNBOOK.md"
    if name == "QUALITY_GATE_CHECKLIST.md":
        return "docs/operations/AUTOMATED_GOVERNANCE.md; docs/operations/VALIDATION_RUNBOOK.md"
    if name == "ARCHITECTURE_GATE_PROOF.md":
        return "docs/architecture/FINAL_REPOSITORY_STRUCTURE.md; docs/operations/AUTOMATED_GOVERNANCE.md"
    if name == "OPENAPI_VALIDATION_PROOF.md":
        return "docs/architecture/OPENAPI_CONTRACT_GOVERNANCE.md; docs/operations/AUTOMATED_GOVERNANCE.md"
    if name == "GITIGNORE_SOURCE_SAFETY_PROOF.md":
        return "docs/architecture/ARCHITECTURE_ENFORCEMENT_CURRENT_STATE.md; docs/architecture/FINAL_REPOSITORY_STRUCTURE.md"
    if name == "PHASE10K8ZGA_PROVIDER_REGISTRY_RUNTIME_BLOCKER_PROOF.md":
        return "tests/test_phase10k8zga_provider_registry_runtime_blocker.py"
    return "docs/architecture/AUDIT_LIFECYCLE_POLICY.md"


def _state_and_action(path: Path) -> tuple[str, str]:
    rel = _relative(path)
    name = path.name
    if rel.startswith("docs/archive/historical_reports/"):
        return "ARCHIVE", "ARCHIVE"
    if name in {
        "ARCHIVED_MIGRATION_TESTS.md",
        "OPTIONAL_CI_READINESS_REPORT.md",
        "SCHEDULER_NAME_ZERO_EXECUTABLE_REF_PROOF.md",
        "TEST_SUITE_ARCHITECTURE_CLEANUP.md",
    }:
        return "ARCHIVE", "ARCHIVE"
    if name in {
        "MISSING_GOVERNANCE_REPORT.md",
        "ACTIVE_RUNTIME_TEST_GATE.md",
    }:
        return "ACTIVE", "KEEP ACTIVE"
    if name in {
        "AUDIT_RETENTION_REGISTER.md",
        "CONTRACT_CONSISTENCY_REPORT.md",
        "OPENAPI_DEPENDENCY_AND_RISK_REPORT.md",
        "TERMINOLOGY_INVENTORY_AND_CLASSIFICATION.md",
        "VENDOR_REFERENCE_CLASSIFICATION.md",
        "ARCHITECTURE_GATE_PROOF.md",
        "OPENAPI_VALIDATION_PROOF.md",
        "GITIGNORE_SOURCE_SAFETY_PROOF.md",
        "PHASE10K8ZGA_PROVIDER_REGISTRY_RUNTIME_BLOCKER_PROOF.md",
    }:
        return "DECISION CAPTURED", "KEEP ACTIVE"
    if name == "QUALITY_GATE_CHECKLIST.md":
        return "ACTIVE", "KEEP ACTIVE"
    return "DECISION CAPTURED", "KEEP ACTIVE"


def _referenced_by(path: Path, state: str) -> str:
    name = path.name
    if state == "ARCHIVE":
        return "historical evidence only"
    if name == "MISSING_GOVERNANCE_REPORT.md":
        return "docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md; docs/architecture/PRODUCTION_READINESS.md"
    if name == "CONTRACT_CONSISTENCY_REPORT.md":
        return "docs/contracts/CONTRACT_INDEX.md"
    if name == "OPENAPI_DEPENDENCY_AND_RISK_REPORT.md":
        return "docs/reports/audits/VENDOR_REFERENCE_CLASSIFICATION.md; docs/reports/audits/TERMINOLOGY_INVENTORY_AND_CLASSIFICATION.md"
    if name == "TERMINOLOGY_INVENTORY_AND_CLASSIFICATION.md":
        return "docs/reports/audits/VENDOR_REFERENCE_CLASSIFICATION.md"
    if name == "VENDOR_REFERENCE_CLASSIFICATION.md":
        return "docs/architecture/VENDOR_NEUTRALITY_AND_OPENAPI_NAMING.md"
    if name == "ACTIVE_RUNTIME_TEST_GATE.md":
        return "tests/test_ops_scripts_contract.py; tests/test_architecture_docs_paths.py"
    if name == "QUALITY_GATE_CHECKLIST.md":
        return "docs/operations/AUTOMATED_GOVERNANCE.md; docs/operations/VALIDATION_RUNBOOK.md"
    if name == "ARCHITECTURE_GATE_PROOF.md":
        return "docs/architecture/FINAL_REPOSITORY_STRUCTURE.md; docs/operations/AUTOMATED_GOVERNANCE.md"
    if name == "OPENAPI_VALIDATION_PROOF.md":
        return "docs/architecture/OPENAPI_CONTRACT_GOVERNANCE.md"
    if name == "GITIGNORE_SOURCE_SAFETY_PROOF.md":
        return "docs/architecture/ARCHITECTURE_ENFORCEMENT_CURRENT_STATE.md"
    if name == "PHASE10K8ZGA_PROVIDER_REGISTRY_RUNTIME_BLOCKER_PROOF.md":
        return "tests/test_phase10k8zga_provider_registry_runtime_blocker.py"
    return "docs/architecture/AUDIT_LIFECYCLE_POLICY.md"


def discover_audit_documents(root: Path = ROOT) -> list[Path]:
    docs: list[Path] = []
    for directory in SCAN_DIRS:
        if not directory.exists():
            continue
        docs.extend(path for path in directory.rglob("*.md") if path.is_file())
    return sorted({path.resolve() for path in docs}, key=lambda p: _relative(p).lower())


def _load_register_entries(register_path: Path) -> dict[str, dict[str, str]]:
    if not register_path.exists():
        return {}
    entries: dict[str, dict[str, str]] = {}
    for line in register_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        if line.startswith("| path ") or line.startswith("| ---"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 6:
            continue
        path, purpose, current_state, decision_captured_where, referenced_by, recommended_action = parts[:6]
        entries[path] = {
            "path": path,
            "purpose": purpose,
            "current_state": current_state,
            "decision_captured_where": decision_captured_where,
            "referenced_by": referenced_by,
            "recommended_action": recommended_action,
        }
    return entries


def build_audit_retention_register(root: Path = ROOT, register_path: Path = REGISTER_PATH) -> str:
    paths = discover_audit_documents(root)
    rows = []
    for path in paths:
        state, action = _state_and_action(path)
        rows.append(
            {
                "path": _relative(path),
                "purpose": _purpose(path),
                "current_state": state,
                "decision_captured_where": _decision_captured_where(path, state),
                "referenced_by": _referenced_by(path, state),
                "recommended_action": action,
            }
        )

    register_rel = _relative(register_path)
    if register_rel not in {row["path"] for row in rows}:
        rows.append(
            {
                "path": register_rel,
                "purpose": _purpose(register_path),
                "current_state": "ACTIVE",
                "decision_captured_where": "docs/architecture/AUDIT_LIFECYCLE_POLICY.md",
                "referenced_by": "docs/reports/audits/*",
                "recommended_action": "KEEP ACTIVE",
            }
        )

    counts = {"ACTIVE": 0, "DECISION CAPTURED": 0, "ARCHIVE": 0, "DELETE CANDIDATE": 0, "DELETE APPROVED": 0}
    for row in rows:
        counts[row["current_state"]] = counts.get(row["current_state"], 0) + 1

    lines = [
        "# Audit Retention Register",
        "",
        "This register classifies audit, checkpoint, proof, and historical report material so the repository can keep useful evidence without letting temporary reports accumulate indefinitely.",
        "",
        f"- register_path: `{_relative(register_path)}`",
        f"- scanned_files: {len(rows)}",
        f"- active: {counts['ACTIVE']}",
        f"- decision_captured: {counts['DECISION CAPTURED']}",
        f"- archive: {counts['ARCHIVE']}",
        f"- delete_candidate: {counts['DELETE CANDIDATE']}",
        f"- delete_approved: {counts['DELETE APPROVED']}",
        "",
        "| path | purpose | current state | decision captured where | referenced by | recommended action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {path} | {purpose} | {current_state} | {decision_captured_where} | {referenced_by} | {recommended_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Policy Note",
            "",
            "Archive entries remain in the retention register so that historical evidence stays visible to reviewers and governance checks.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_audit_retention_register(root: Path = ROOT, register_path: Path = REGISTER_PATH) -> Path:
    content = build_audit_retention_register(root=root, register_path=register_path)
    register_path.parent.mkdir(parents=True, exist_ok=True)
    register_path.write_text(content, encoding="utf-8")
    return register_path


def collect_audit_lifecycle_report(root: Path = ROOT, register_path: Path = REGISTER_PATH) -> dict[str, Any]:
    discovered = discover_audit_documents(root)
    register_entries = _load_register_entries(register_path)
    discovered_rel = {_relative(path) for path in discovered}
    register_paths = set(register_entries)
    missing_from_register = sorted(discovered_rel - register_paths)
    register_only = sorted(register_paths - discovered_rel)

    warnings: list[str] = []
    clear_violations: list[str] = []

    if register_path.exists() and not register_entries:
        clear_violations.append(f"unable_to_parse_register:{_relative(register_path)}")
    if len(register_only) > 0:
        warnings.append(f"register_has_extra_entries:{len(register_only)}")
    if len(missing_from_register) > 0:
        warnings.append(f"missing_register_entries:{len(missing_from_register)}")

    for path_text, row in register_entries.items():
        if row.get("current_state") == "ACTIVE" and not row.get("decision_captured_where"):
            warnings.append(f"active_without_decision:{path_text}")

    active_paths = [row for row in register_entries.values() if row.get("current_state") == "ACTIVE"]
    advisory_paths = [row for row in register_entries.values() if row.get("current_state") == "DECISION CAPTURED"]
    archive_paths = [row for row in register_entries.values() if row.get("current_state") == "ARCHIVE"]
    delete_candidates = [row for row in register_entries.values() if row.get("current_state") == "DELETE CANDIDATE"]
    delete_approved = [row for row in register_entries.values() if row.get("current_state") == "DELETE APPROVED"]

    status = "ok" if not warnings else "advisory"
    ok = not clear_violations
    return {
        "ok": ok,
        "status": status if ok else "violation",
        "register_path": _relative(register_path),
        "scanned_count": len(discovered_rel),
        "register_count": len(register_entries),
        "missing_from_register": missing_from_register,
        "register_only": register_only,
        "active_count": len(active_paths),
        "decision_captured_count": len(advisory_paths),
        "archive_count": len(archive_paths),
        "delete_candidate_count": len(delete_candidates),
        "delete_approved_count": len(delete_approved),
        "warnings": warnings,
        "clear_violations": clear_violations,
        "register_entries": register_entries,
    }


def _render_text(report: dict[str, Any]) -> str:
    lines = [
        "audit_lifecycle: {status}".format(status=report.get("status")),
        f"register_path: {report.get('register_path')}",
        f"scanned_count: {report.get('scanned_count')}",
        f"register_count: {report.get('register_count')}",
        f"active_count: {report.get('active_count')}",
        f"decision_captured_count: {report.get('decision_captured_count')}",
        f"archive_count: {report.get('archive_count')}",
        f"delete_candidate_count: {report.get('delete_candidate_count')}",
        f"delete_approved_count: {report.get('delete_approved_count')}",
        f"missing_from_register: {len(report.get('missing_from_register') or [])}",
        f"register_only: {len(report.get('register_only') or [])}",
        f"warnings: {len(report.get('warnings') or [])}",
        f"clear_violations: {len(report.get('clear_violations') or [])}",
    ]
    for item in (report.get("warnings") or [])[:10]:
        lines.append(f"- warning: {item}")
    for item in (report.get("clear_violations") or [])[:10]:
        lines.append(f"- violation: {item}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit lifecycle governance checker.")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--register-path", default=str(REGISTER_PATH))
    parser.add_argument("--write-register", action="store_true")
    args = parser.parse_args(argv)

    register_path = Path(args.register_path)
    if not register_path.is_absolute():
        register_path = ROOT / register_path
    if args.write_register:
        write_audit_retention_register(root=ROOT, register_path=register_path)

    report = collect_audit_lifecycle_report(root=ROOT, register_path=register_path)
    if args.output == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    return 2 if report.get("clear_violations") else 0


if __name__ == "__main__":
    raise SystemExit(main())
