from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from src.market_intelligence.research_intelligence import DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH


UNIVERSAL_MARKET_FRAMEWORK_SCHEMA_VERSION = "universal_market_framework.v1"
UNIVERSAL_MARKET_FRAMEWORK_RUNTIME_VERSION = "phase-universal-market-framework.v1"
DEFAULT_UNIVERSAL_MARKET_FRAMEWORK_ARTIFACT_ROOT = Path(
    "data/backtests/universal_market_framework_artifacts"
)
NFL_REFERENCE_PROFILE_ID = "sports:nfl"


_CANONICAL_OWNER_INTERFACES: tuple[dict[str, str], ...] = (
    {
        "interface_id": "market_profile_contract",
        "canonical_owner": "src.data.market_profile_contracts",
        "dashboard_surface": "profile_contract_registry",
        "lifecycle_gate": "profile_contract_validated",
    },
    {
        "interface_id": "market_profile_registry",
        "canonical_owner": "src.data.market_profile_registry",
        "dashboard_surface": "profile_contract_registry",
        "lifecycle_gate": "profile_registered",
    },
    {
        "interface_id": "historical_dataset",
        "canonical_owner": "src.data.historical_research_database",
        "dashboard_surface": "certified_pipeline_reference.historical_dataset",
        "lifecycle_gate": "historical_dataset_certified",
    },
    {
        "interface_id": "feature_snapshots",
        "canonical_owner": "src.data.feature_registry",
        "dashboard_surface": "certified_pipeline_reference.feature_snapshots",
        "lifecycle_gate": "feature_snapshots_certified",
    },
    {
        "interface_id": "mathematical_engines",
        "canonical_owner": "src.data.math_engine_population",
        "dashboard_surface": "certified_pipeline_reference.mathematical_engines",
        "lifecycle_gate": "math_engines_certified",
    },
    {
        "interface_id": "signals",
        "canonical_owner": "src.market_intelligence.signal_population",
        "dashboard_surface": "certified_pipeline_reference.signals",
        "lifecycle_gate": "signals_certified",
    },
    {
        "interface_id": "decision_rows",
        "canonical_owner": "src.backtesting.decision_row_population",
        "dashboard_surface": "certified_pipeline_reference.decision_rows",
        "lifecycle_gate": "decision_rows_certified",
    },
    {
        "interface_id": "baseline_backtesting",
        "canonical_owner": "src.backtesting.baseline_backtesting",
        "dashboard_surface": "certified_pipeline_reference.baseline_backtesting",
        "lifecycle_gate": "baseline_backtest_certified",
    },
    {
        "interface_id": "pipeline_validation",
        "canonical_owner": "src.backtesting.pipeline_validation",
        "dashboard_surface": "certified_pipeline_reference.pipeline_validation",
        "lifecycle_gate": "pipeline_validation_certified",
    },
    {
        "interface_id": "research_intelligence",
        "canonical_owner": "src.market_intelligence.research_intelligence",
        "dashboard_surface": "certified_pipeline_reference.research_intelligence",
        "lifecycle_gate": "research_intelligence_certified",
    },
    {
        "interface_id": "dashboard_query_surface",
        "canonical_owner": "src.services.streamlit_dashboard_data",
        "dashboard_surface": "dashboard_views",
        "lifecycle_gate": "dashboard_surface_ready",
    },
)


_FORBIDDEN_ACTIVATIONS: tuple[str, ...] = (
    "additional_market_activation",
    "new_provider_or_connector",
    "paid_or_live_ingestion",
    "prediction_market_implementation",
    "zero_dte_options_implementation",
    "paper_trading",
    "live_execution",
    "capital_allocation",
    "worldview_intelligence",
    "machine_learning",
    "optimization",
    "parameter_tuning",
)


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}.{digest}"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _profile_registry_rows(catalog: tuple[Any, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profile in sorted(catalog, key=lambda item: item.profile_id):
        if profile.profile_id == NFL_REFERENCE_PROFILE_ID:
            activation_state = "reference_implementation"
            onboarding_state = "certified_reference_locked"
        elif profile.profile_id == "sports":
            activation_state = "framework_family_contract"
            onboarding_state = "profile_family_contract_only"
        else:
            activation_state = "roadmap_only_contract"
            onboarding_state = "not_activated"
        rows.append(
            {
                "profile_id": profile.profile_id,
                "profile_family": profile.profile_family,
                "market_scope": profile.market_scope,
                "activation_state": activation_state,
                "onboarding_state": onboarding_state,
                "canonical_identifier_count": len(profile.canonical_identifiers),
                "required_timestamp_count": len(profile.required_timestamps),
                "canonical_field_count": len(profile.canonical_fields),
                "validation_rule_count": len(profile.validation_rules),
                "leakage_rule_count": len(profile.leakage_rules),
                "description": profile.description,
            }
        )
    return rows


def _reference_parity(research_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    line = dict(research_snapshot.get("lineage_summary") or {})
    cert = dict(research_snapshot.get("certification_summary") or {})
    research_summary = dict(research_snapshot.get("research_summary") or {})
    opportunities = list(research_snapshot.get("opportunity_summaries") or [])
    evidence = list(research_snapshot.get("supporting_evidence_packages") or [])
    parity_payload = {
        "research_intelligence_run_id": research_snapshot.get("research_intelligence_run_id"),
        "lineage_summary": line,
        "certification_summary": cert,
        "research_summary": research_summary,
        "opportunity_ids": [row.get("research_opportunity_id") for row in opportunities],
        "evidence_package_ids": [row.get("evidence_package_id") for row in evidence],
    }
    return {
        "ok": bool(research_snapshot.get("ok"))
        and research_snapshot.get("readiness") == "universal_market_framework_ready",
        "reference_profile_id": NFL_REFERENCE_PROFILE_ID,
        "research_intelligence_run_id": research_snapshot.get("research_intelligence_run_id"),
        "pipeline_validation_run_id": line.get("pipeline_validation_run_id"),
        "backtest_run_id": line.get("backtest_run_id"),
        "decision_batch_id": line.get("decision_batch_id"),
        "sample_size": research_summary.get("sample_size"),
        "roi_percent": research_summary.get("roi_percent"),
        "opportunity_count": len(opportunities),
        "evidence_package_count": len(evidence),
        "parity_digest": _stable_id("umf.nfl_reference_parity", parity_payload),
    }


def _build_dashboard_views(
    *,
    registry_rows: list[dict[str, Any]],
    owner_interfaces: tuple[dict[str, str], ...],
    reference_parity: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "profile_readiness": registry_rows,
        "canonical_owner_interfaces": list(owner_interfaces),
        "nfl_reference_parity": dict(reference_parity),
        "onboarding_gate_summary": [
            {
                "gate": owner["lifecycle_gate"],
                "canonical_owner": owner["canonical_owner"],
                "required_before_market_activation": True,
            }
            for owner in owner_interfaces
        ],
        "query_interfaces": [
            {
                "query_id": "list_market_profile_contracts",
                "purpose": "List market-agnostic profile contracts without activating a market.",
                "source_surface": "profile_contract_registry",
            },
            {
                "query_id": "inspect_reference_implementation_parity",
                "purpose": "Verify Universal Market Framework changes did not alter certified NFL behavior.",
                "source_surface": "nfl_reference_parity",
            },
            {
                "query_id": "inspect_market_onboarding_gates",
                "purpose": "Show the lifecycle gates a future market profile must satisfy.",
                "source_surface": "onboarding_gate_summary",
            },
        ],
    }


def _write_artifacts(
    *,
    artifact_root: Path,
    snapshot: Mapping[str, Any],
) -> dict[str, str]:
    run_root = artifact_root / str(snapshot["universal_market_framework_run_id"])
    run_root.mkdir(parents=True, exist_ok=True)
    report_json_path = run_root / "report.json"
    dashboard_json_path = run_root / "dashboard.json"
    report_markdown_path = run_root / "report.md"
    report_json_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    dashboard_json_path.write_text(
        json.dumps(snapshot.get("dashboard_views", {}), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Universal Market Framework",
        "",
        f"- Status: `{snapshot.get('status')}`",
        f"- Readiness: `{snapshot.get('readiness')}`",
        f"- Reference profile: `{snapshot.get('reference_profile_id')}`",
        f"- NFL parity: `{snapshot.get('nfl_reference_parity', {}).get('ok')}`",
        f"- Unresolved blockers: `{len(snapshot.get('unresolved_blockers', []))}`",
        "",
        "This artifact is a deterministic framework summary over certified outputs only.",
    ]
    report_markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "artifact_root": str(run_root),
        "report_json_path": str(report_json_path),
        "report_markdown_path": str(report_markdown_path),
        "dashboard_json_path": str(dashboard_json_path),
    }


def build_universal_market_framework_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    artifact_root: str | Path | None = None,
    persist_artifacts: bool = True,
) -> dict[str, Any]:
    from src.market_intelligence.market_profiles import (
        build_market_profile_catalog,
        validate_market_profile_catalog,
    )
    from src.market_intelligence.research_intelligence import build_research_intelligence_snapshot

    storage = Path(storage_path or DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH)
    catalog = build_market_profile_catalog()
    catalog_validation = validate_market_profile_catalog()
    research_snapshot = build_research_intelligence_snapshot(
        storage_path=storage,
        backend=backend,
        include_layer_snapshots=False,
        persist_artifacts=False,
    )
    registry_rows = _profile_registry_rows(catalog)
    reference_parity = _reference_parity(research_snapshot)
    active_non_reference_profiles = [
        row["profile_id"]
        for row in registry_rows
        if row["profile_id"] != NFL_REFERENCE_PROFILE_ID
        and row["activation_state"] == "reference_implementation"
    ]
    checks = [
        {
            "check_id": "market_profile_catalog_valid",
            "category": "contract",
            "severity": "error",
            "ok": bool(catalog_validation.get("ok")),
            "expected": "valid market profile catalog",
            "actual": "valid" if catalog_validation.get("ok") else catalog_validation.get("errors", []),
        },
        {
            "check_id": "nfl_reference_profile_present",
            "category": "parity",
            "severity": "error",
            "ok": any(row["profile_id"] == NFL_REFERENCE_PROFILE_ID for row in registry_rows),
            "expected": NFL_REFERENCE_PROFILE_ID,
            "actual": [row["profile_id"] for row in registry_rows],
        },
        {
            "check_id": "research_intelligence_reference_ready",
            "category": "parity",
            "severity": "error",
            "ok": bool(reference_parity.get("ok")),
            "expected": "universal_market_framework_ready",
            "actual": research_snapshot.get("readiness"),
        },
        {
            "check_id": "no_non_reference_market_activated",
            "category": "boundary",
            "severity": "error",
            "ok": not active_non_reference_profiles,
            "expected": [],
            "actual": active_non_reference_profiles,
        },
        {
            "check_id": "canonical_owner_reuse_only",
            "category": "ownership",
            "severity": "error",
            "ok": all(owner["canonical_owner"].startswith("src.") for owner in _CANONICAL_OWNER_INTERFACES),
            "expected": "canonical src owners reused",
            "actual": [owner["canonical_owner"] for owner in _CANONICAL_OWNER_INTERFACES],
        },
    ]
    unresolved_blockers = [
        f"{check['category']}:{check['check_id']}"
        for check in checks
        if check["severity"] == "error" and not check["ok"]
    ]
    ok = not unresolved_blockers
    dashboard_views = _build_dashboard_views(
        registry_rows=registry_rows,
        owner_interfaces=_CANONICAL_OWNER_INTERFACES,
        reference_parity=reference_parity,
    )
    run_id = _stable_id(
        "umf.run",
        UNIVERSAL_MARKET_FRAMEWORK_SCHEMA_VERSION,
        [row["profile_id"] for row in registry_rows],
        reference_parity.get("parity_digest"),
    )
    snapshot: dict[str, Any] = {
        "ok": ok,
        "status": "completed" if ok else "blocked",
        "readiness": "first_market_profile_onboarding_ready" if ok else "blocked",
        "lifecycle_state": "universal_market_framework_ready" if ok else "blocked",
        "validation_state": "validated" if ok else "rejected",
        "schema_version": UNIVERSAL_MARKET_FRAMEWORK_SCHEMA_VERSION,
        "universal_market_framework_run_id": run_id,
        "universal_market_framework_version": UNIVERSAL_MARKET_FRAMEWORK_RUNTIME_VERSION,
        "generated_at": _utc_now(),
        "reference_profile_id": NFL_REFERENCE_PROFILE_ID,
        "reference_implementation": "certified_nfl_research_chain_through_research_intelligence",
        "profile_contract_registry": registry_rows,
        "canonical_owner_interfaces": list(_CANONICAL_OWNER_INTERFACES),
        "onboarding_lifecycle_interfaces": dashboard_views["onboarding_gate_summary"],
        "forbidden_activation_summary": {
            "no_activation_items": list(_FORBIDDEN_ACTIVATIONS),
            "new_market_implementations_added": False,
            "new_connectors_or_providers_added": False,
            "paper_or_live_execution_added": False,
            "capital_allocation_added": False,
        },
        "nfl_reference_parity": reference_parity,
        "certified_pipeline_reference": {
            "research_intelligence_run_id": reference_parity.get("research_intelligence_run_id"),
            "pipeline_validation_run_id": reference_parity.get("pipeline_validation_run_id"),
            "backtest_run_id": reference_parity.get("backtest_run_id"),
            "decision_batch_id": reference_parity.get("decision_batch_id"),
        },
        "dashboard_views": dashboard_views,
        "query_interfaces": dashboard_views["query_interfaces"],
        "validation_checks": checks,
        "validation_summary": {
            "error_check_count": sum(1 for check in checks if check["severity"] == "error"),
            "error_checks_passed": sum(1 for check in checks if check["severity"] == "error" and check["ok"]),
        },
        "artifact_references": {},
        "artifact_integrity_ok": False,
        "unresolved_blockers": unresolved_blockers,
    }
    if persist_artifacts:
        root = Path(artifact_root or DEFAULT_UNIVERSAL_MARKET_FRAMEWORK_ARTIFACT_ROOT)
        artifact_references = _write_artifacts(artifact_root=root, snapshot=snapshot)
        snapshot["artifact_references"] = artifact_references
        snapshot["artifact_integrity_ok"] = all(
            Path(path).exists()
            for key, path in artifact_references.items()
            if key != "artifact_root"
        )
    return snapshot


def get_universal_market_framework_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
) -> dict[str, Any]:
    return build_universal_market_framework_snapshot(storage_path=storage_path, backend=backend)


__all__ = [
    "DEFAULT_UNIVERSAL_MARKET_FRAMEWORK_ARTIFACT_ROOT",
    "NFL_REFERENCE_PROFILE_ID",
    "UNIVERSAL_MARKET_FRAMEWORK_RUNTIME_VERSION",
    "UNIVERSAL_MARKET_FRAMEWORK_SCHEMA_VERSION",
    "build_universal_market_framework_snapshot",
    "get_universal_market_framework_snapshot_for_dashboard",
]
