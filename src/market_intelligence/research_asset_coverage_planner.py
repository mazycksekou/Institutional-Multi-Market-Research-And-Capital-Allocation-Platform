from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.data.data_paths import get_runtime_data_path
from src.data.data_source_registry import build_registry, build_registry_report, recommended_next_adapters
from src.data.historical_research_asset_certification_runtime import (
    DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID,
    HistoricalResearchAssetCertificationRuntime,
)
from src.data.nfl_open_data_source_exhaustion import nfl_candidate_sources
from src.data.nfl_open_data_sources import nfl_open_data_sources
from src.data.research_asset_lifecycle_runtime import ResearchAssetLifecycleRuntime
from src.data.source_quality_scoring import quality_tier, score_source
from src.market_intelligence.nfl_coaching_sources import nfl_coaching_sources
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine


RESEARCH_ASSET_COVERAGE_PLANNER_SCHEMA_VERSION = "src.market_intelligence.research_asset_coverage_planner.v1"
DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH = get_runtime_data_path(
    "research_asset_coverage_planner",
    "canonical_data.sqlite",
)
DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_DATASET_NAME = "research_asset_coverage_planner"
DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID = DEFAULT_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_PROFILE_ID
DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_OWNER = "src.market_intelligence"

_SOURCE_ACCESS_COST_SCORES = {
    "open_dataset": 95.0,
    "open_public": 92.0,
    "manual_import": 90.0,
    "open_github_file": 86.0,
    "free_key": 74.0,
    "free_tier": 68.0,
    "public_wrapper_with_terms_review": 56.0,
    "rest_api": 52.0,
    "third_party_release": 42.0,
    "paid_candidate": 28.0,
    "partner_candidate": 26.0,
    "institutional_vendor_candidate": 24.0,
    "broker_data_candidate": 24.0,
    "sportsbook_account_candidate": 22.0,
    "internal_proprietary_candidate": 20.0,
    "future_only": 18.0,
    "unknown": 10.0,
}

_SOURCE_ACCESS_REPRODUCIBILITY_SCORES = {
    "open_dataset": 95.0,
    "open_public": 90.0,
    "manual_import": 92.0,
    "open_github_file": 88.0,
    "free_key": 74.0,
    "free_tier": 68.0,
    "public_wrapper_with_terms_review": 54.0,
    "rest_api": 50.0,
    "third_party_release": 46.0,
    "paid_candidate": 30.0,
    "partner_candidate": 28.0,
    "institutional_vendor_candidate": 26.0,
    "broker_data_candidate": 24.0,
    "sportsbook_account_candidate": 22.0,
    "internal_proprietary_candidate": 20.0,
    "future_only": 18.0,
    "unknown": 10.0,
}

_SOURCE_ACCESS_POINT_IN_TIME_SCORES = {
    "open_dataset": 96.0,
    "open_public": 92.0,
    "manual_import": 94.0,
    "open_github_file": 84.0,
    "free_key": 78.0,
    "free_tier": 74.0,
    "public_wrapper_with_terms_review": 60.0,
    "rest_api": 58.0,
    "third_party_release": 52.0,
    "paid_candidate": 30.0,
    "partner_candidate": 28.0,
    "institutional_vendor_candidate": 26.0,
    "broker_data_candidate": 24.0,
    "sportsbook_account_candidate": 22.0,
    "internal_proprietary_candidate": 20.0,
    "future_only": 18.0,
    "unknown": 10.0,
}

_SOURCE_ACCESS_LICENSE_SCORES = {
    "open_dataset": 96.0,
    "open_public": 94.0,
    "manual_import": 92.0,
    "open_github_file": 84.0,
    "free_key": 76.0,
    "free_tier": 70.0,
    "public_wrapper_with_terms_review": 56.0,
    "rest_api": 54.0,
    "third_party_release": 46.0,
    "paid_candidate": 30.0,
    "partner_candidate": 28.0,
    "institutional_vendor_candidate": 26.0,
    "broker_data_candidate": 24.0,
    "sportsbook_account_candidate": 22.0,
    "internal_proprietary_candidate": 20.0,
    "future_only": 18.0,
    "unknown": 10.0,
}

_SOURCE_ACCESS_RELIABILITY_SCORES = {
    "open_dataset": 90.0,
    "open_public": 88.0,
    "manual_import": 84.0,
    "open_github_file": 78.0,
    "free_key": 74.0,
    "free_tier": 68.0,
    "public_wrapper_with_terms_review": 58.0,
    "rest_api": 56.0,
    "third_party_release": 42.0,
    "paid_candidate": 28.0,
    "partner_candidate": 26.0,
    "institutional_vendor_candidate": 24.0,
    "broker_data_candidate": 24.0,
    "sportsbook_account_candidate": 22.0,
    "internal_proprietary_candidate": 20.0,
    "future_only": 18.0,
    "unknown": 12.0,
}

_SOURCE_CADENCE_SCORES = {
    "live": 100.0,
    "near_live": 88.0,
    "daily": 74.0,
    "weekly": 56.0,
    "seasonal": 40.0,
    "historical_only": 36.0,
    "manual": 72.0,
    "unknown": 18.0,
}

_CERTIFIED_SOURCE_ROLES = {"nflverse", "nflreadr", "nflfastr", "open_meteo", "national_weather_service", "noaa_public_datasets", "the_odds_api"}
_LOCAL_FIXTURE_ROLES = {"local_fixture", "manual_fixture"}
_MANUAL_SOURCE_ROLES = {"manual_import", "manual_schedule_import", "manual_csv", "local_fixture", "manual_fixture"}
_CROSS_CUTTING_SOURCE_IDS = {
    "the_odds_api",
    "sportsgameodds",
    "odds_api_io",
    "oddsmagnet",
    "open_meteo",
    "national_weather_service",
    "weatherstack",
    "weatherapi",
    "noaa_public_datasets",
    "open_meteo_forecast",
    "open_meteo_historical",
    "open_meteo_stadium_weather",
    "the_odds_api_market",
}


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


def _normalize_items(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        values = (values,)
    return tuple(item for item in (_normalize_text(value) for value in values) if item)


def _normalize_components(values: Any) -> tuple[str, ...]:
    return _normalize_items(values)


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

    return json.dumps(value, default=default, sort_keys=True, ensure_ascii=False)


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _merge_non_empty(base: dict[str, Any], update: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in update.items():
        if value in (None, "", (), [], {}, set()):
            continue
        if key == "source_aliases":
            aliases = set(_normalize_items(merged.get("source_aliases")))
            aliases.update(_normalize_items(value))
            merged["source_aliases"] = sorted(aliases)
            continue
        merged[key] = value
    return merged


def _asset_profile_fields(profile_id: str) -> dict[str, str]:
    if profile_id != DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID:
        return {"market_profile": profile_id, "market_family": "unknown"}
    return {"market_profile": profile_id, "market_family": "sports"}


def _cadence_score(source: Mapping[str, Any]) -> float:
    cadence = _normalize_text(
        source.get("cadence")
        or source.get("freshness", {}).get("expected_update_cadence")
        or source.get("update_frequency")
        or "unknown",
        "unknown",
    ).lower()
    return _SOURCE_CADENCE_SCORES.get(cadence, _SOURCE_CADENCE_SCORES["unknown"])


def _source_access_score(source: Mapping[str, Any], mapping: dict[str, float]) -> float:
    access = _normalize_text(source.get("source_access_type") or "unknown", "unknown").lower()
    return mapping.get(access, mapping["unknown"])


def _source_quality_snapshot(source: Mapping[str, Any], required_inputs: Sequence[str]) -> dict[str, Any]:
    candidate = dict(source)
    candidate.setdefault("coverage", {})
    candidate.setdefault("freshness", {})
    candidate.setdefault("limits", {})
    candidate.setdefault("legal_terms", {})
    candidate.setdefault("model_mapping", {})
    candidate["freshness"].setdefault("expected_update_cadence", source.get("cadence") or "unknown")
    candidate["limits"].setdefault("rate_limit_known", candidate.get("source_access_type") not in {"open_dataset", "manual_import", "open_public"})
    candidate["legal_terms"].setdefault("requires_manual_review", bool(source.get("requires_terms_review")))
    candidate["model_mapping"].setdefault("model_inputs_supported", list(required_inputs))
    return score_source(candidate, required_inputs=list(required_inputs))


def _source_identifier(source: Mapping[str, Any]) -> str:
    return _normalize_text(source.get("source_id") or source.get("provider_id") or source.get("source_name"))


def _source_name(source: Mapping[str, Any]) -> str:
    return _normalize_text(source.get("source_name") or source.get("display_name") or source.get("source_id"))


def _provider_role_from_access(source: Mapping[str, Any]) -> str:
    access = _normalize_text(source.get("source_access_type") or "unknown", "unknown").lower()
    if access in {"open_dataset", "open_public", "manual_import", "open_github_file"}:
        return "primary_acquisition"
    if access in {"free_key", "free_tier"}:
        return "verification_source"
    if access in {"public_wrapper_with_terms_review", "rest_api"}:
        return "verification_source"
    if access in {"paid_candidate", "partner_candidate", "institutional_vendor_candidate", "broker_data_candidate", "sportsbook_account_candidate", "internal_proprietary_candidate"}:
        return "future_enrichment"
    if source.get("approval_status") in {"blocked", "redundant_skip"}:
        return "future_enrichment"
    return "fallback_source"


def _build_provider_score(source: Mapping[str, Any], *, coverage_components: Sequence[str], required_components: Sequence[str], required_inputs: Sequence[str]) -> dict[str, Any]:
    access = _normalize_text(source.get("source_access_type") or "unknown", "unknown").lower()
    coverage_components = _normalize_components(coverage_components)
    required_components = _normalize_components(required_components)
    required_inputs = _normalize_items(required_inputs)
    coverage_ratio = len(set(coverage_components) & set(required_components)) / max(len(required_components), 1)
    source_quality = _source_quality_snapshot(source, required_inputs)
    coverage_score = max(_normalize_float(source_quality.get("coverage_score")) or 0.0, coverage_ratio * 100.0)
    historical_depth_score = max(
        _normalize_float(source_quality.get("historical_depth_score")) or 0.0,
        92.0 if source.get("coverage", {}).get("historical") or "historical" in coverage_components else 62.0,
    )
    point_in_time_safety_score = max(
        _normalize_float(source_quality.get("freshness_score")) or 0.0,
        _source_access_score(source, _SOURCE_ACCESS_POINT_IN_TIME_SCORES),
    )
    licensing_score = max(
        100.0 - _normalize_float(source_quality.get("terms_risk_score")),
        _source_access_score(source, _SOURCE_ACCESS_LICENSE_SCORES),
    )
    reliability_score = max(
        _normalize_float(source_quality.get("source_reliability_score")) or 0.0,
        _source_access_score(source, _SOURCE_ACCESS_RELIABILITY_SCORES),
    )
    cost_score = _source_access_score(source, _SOURCE_ACCESS_COST_SCORES)
    update_frequency_score = _cadence_score(source)
    reproducibility_score = _source_access_score(source, _SOURCE_ACCESS_REPRODUCIBILITY_SCORES)
    certification_suitability_score = round(
        (
            coverage_score * 0.25
            + historical_depth_score * 0.12
            + point_in_time_safety_score * 0.15
            + licensing_score * 0.12
            + reliability_score * 0.16
            + cost_score * 0.06
            + update_frequency_score * 0.06
            + reproducibility_score * 0.08
        ),
        2,
    )
    selection_score = round(
        (
            coverage_score * 0.33
            + historical_depth_score * 0.11
            + point_in_time_safety_score * 0.12
            + licensing_score * 0.08
            + reliability_score * 0.14
            + cost_score * 0.07
            + update_frequency_score * 0.05
            + reproducibility_score * 0.05
            + certification_suitability_score * 0.05
        ),
        2,
    )
    quality_tier_value = quality_tier(source_quality, dict(source))
    return {
        "source_quality_snapshot": source_quality,
        "coverage_score": round(coverage_score, 2),
        "historical_depth_score": round(historical_depth_score, 2),
        "point_in_time_safety_score": round(point_in_time_safety_score, 2),
        "licensing_score": round(licensing_score, 2),
        "reliability_score": round(reliability_score, 2),
        "cost_score": round(cost_score, 2),
        "update_frequency_score": round(update_frequency_score, 2),
        "reproducibility_score": round(reproducibility_score, 2),
        "certification_suitability_score": round(certification_suitability_score, 2),
        "selection_score": round(selection_score, 2),
        "quality_tier": quality_tier_value,
        "provider_role": _provider_role_from_access(source),
        "current_phase_allowed": bool(source.get("current_phase_allowed", False)),
        "approval_status": _normalize_text(source.get("approval_status"), "candidate"),
        "source_access_type": access,
    }


def _required_source_fields_for_asset(asset_id: str) -> tuple[str, ...]:
    return _normalize_items(_NFL_ASSET_BLUEPRINTS.get(asset_id, {}).get("required_inputs", ()))


def _build_provider_record(provider_id: str, provider_source: Mapping[str, Any], asset_blueprints: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    supported_assets: list[str] = []
    asset_coverage_map: dict[str, Any] = {}
    best_fit_score = 0.0
    best_fit_asset = ""
    source_aliases = set(_normalize_items(provider_source.get("source_aliases")))
    if provider_id == _normalize_text(provider_source.get("source_id")):
        source_aliases.add(provider_id)
    for asset in asset_blueprints:
        asset_id = _normalize_text(asset.get("research_asset_id"))
        provider_entry = dict((asset.get("provider_candidates") or {}).get(provider_id, {}))
        if not provider_entry and provider_id not in asset.get("provider_candidates", {}):
            continue
        coverage_components = _normalize_components(provider_entry.get("coverage_components") or ())
        if not coverage_components and provider_entry.get("coverage"):
            coverage_components = tuple(sorted(_normalize_items(provider_entry.get("coverage"))))
        if not coverage_components:
            continue
        supported_assets.append(asset_id)
        score = _build_provider_score(
            provider_source,
            coverage_components=coverage_components,
            required_components=asset.get("required_components", ()),
            required_inputs=asset.get("required_inputs", ()),
        )
        asset_coverage_map[asset_id] = {
            "research_asset_id": asset_id,
            "research_asset_name": asset.get("research_asset_name", asset_id),
            "asset_category": asset.get("asset_category", "dataset"),
            "asset_type": asset.get("asset_type", "table_snapshot"),
            "provider_role": _normalize_text(provider_entry.get("provider_role"), score["provider_role"]),
            "coverage_components": list(coverage_components),
            "missing_components": [],
            "coverage_score": score["coverage_score"],
            "historical_depth_score": score["historical_depth_score"],
            "point_in_time_safety_score": score["point_in_time_safety_score"],
            "licensing_score": score["licensing_score"],
            "reliability_score": score["reliability_score"],
            "cost_score": score["cost_score"],
            "update_frequency_score": score["update_frequency_score"],
            "reproducibility_score": score["reproducibility_score"],
            "certification_suitability_score": score["certification_suitability_score"],
            "selection_score": score["selection_score"],
            "quality_tier": score["quality_tier"],
            "source_quality_snapshot": score["source_quality_snapshot"],
            "notes": _normalize_text(provider_entry.get("notes")),
        }
        if score["selection_score"] > best_fit_score:
            best_fit_score = float(score["selection_score"])
            best_fit_asset = asset_id
    provider_quality = _build_provider_score(
        provider_source,
        coverage_components=tuple(sorted({component for asset in asset_coverage_map.values() for component in asset["coverage_components"]})),
        required_components=tuple(sorted({component for asset in asset_coverage_map.values() for component in asset["coverage_components"]})),
        required_inputs=(),
    )
    future_candidate = bool(
        provider_source.get("future_source_candidate")
        or provider_source.get("future_paid_candidate")
        or provider_source.get("approval_status") in {"blocked", "redundant_skip"}
        or provider_source.get("current_phase_allowed") is False
        or provider_source.get("source_access_type") in {"paid_candidate", "partner_candidate", "institutional_vendor_candidate", "broker_data_candidate", "sportsbook_account_candidate", "internal_proprietary_candidate", "future_only"}
    )
    return {
        "provider_id": provider_id,
        "provider_name": _source_name(provider_source),
        "source_family": _normalize_text(provider_source.get("source_family")),
        "source_category": _normalize_text(provider_source.get("source_category") or provider_source.get("category") or ""),
        "data_categories": list(_normalize_items(provider_source.get("data_categories") or provider_source.get("candidate_data_categories") or provider_source.get("data_category"))),
        "source_access_type": _normalize_text(provider_source.get("source_access_type") or provider_source.get("source_kind") or "unknown", "unknown"),
        "source_kind": _normalize_text(provider_source.get("source_kind")),
        "approval_status": _normalize_text(provider_source.get("approval_status"), "candidate"),
        "current_phase_allowed": bool(provider_source.get("current_phase_allowed", provider_source.get("enabled", False))),
        "future_source_candidate": bool(provider_source.get("future_source_candidate", provider_source.get("future_paid_candidate", False))),
        "supported_assets": supported_assets,
        "asset_coverage_map": asset_coverage_map,
        "coverage_score": provider_quality["coverage_score"],
        "historical_depth_score": provider_quality["historical_depth_score"],
        "point_in_time_safety_score": provider_quality["point_in_time_safety_score"],
        "licensing_score": provider_quality["licensing_score"],
        "reliability_score": provider_quality["reliability_score"],
        "cost_score": provider_quality["cost_score"],
        "update_frequency_score": provider_quality["update_frequency_score"],
        "reproducibility_score": provider_quality["reproducibility_score"],
        "certification_suitability_score": provider_quality["certification_suitability_score"],
        "selection_score": provider_quality["selection_score"],
        "quality_tier": provider_quality["quality_tier"],
        "provider_role": provider_quality["provider_role"],
        "best_fit_asset_id": best_fit_asset,
        "future_candidate": future_candidate,
        "source_aliases": sorted(source_aliases),
        "source_quality_snapshot": provider_quality["source_quality_snapshot"],
        "notes": _normalize_text(provider_source.get("notes")),
    }


def _provider_bundle_from_candidates(candidate_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(candidate_records, key=lambda row: (-float(row.get("selection_score") or 0.0), _normalize_text(row.get("provider_id"))))
    primary = ordered[0] if ordered else {}
    verification = ordered[1] if len(ordered) > 1 else {}
    fallback = ordered[2] if len(ordered) > 2 else {}
    enrichment = ordered[3:] if len(ordered) > 3 else []
    selected_provider_ids = [item["provider_id"] for item in ordered[:4] if item.get("provider_id")]
    coverage_components = sorted({component for item in ordered for component in item.get("coverage_components", [])})
    return {
        "selected_provider_ids": selected_provider_ids,
        "primary_provider_id": primary.get("provider_id", ""),
        "verification_provider_id": verification.get("provider_id", ""),
        "fallback_provider_id": fallback.get("provider_id", ""),
        "enrichment_provider_ids": [item.get("provider_id", "") for item in enrichment if item.get("provider_id")],
        "selection_score": round(sum(float(item.get("selection_score") or 0.0) for item in ordered[:4]) / max(len(ordered[:4]), 1), 2) if ordered else 0.0,
        "coverage_components": coverage_components,
        "provider_roles": {
            "primary": primary.get("provider_role", ""),
            "verification": verification.get("provider_role", ""),
            "fallback": fallback.get("provider_role", ""),
            "enrichment": [item.get("provider_role", "") for item in enrichment if item.get("provider_role")],
        },
        "provider_candidates": [dict(item) for item in ordered],
    }


def _latest_row(rows: Sequence[Mapping[str, Any]], *, key_name: str, key_value: str, order_field: str = "updated_at") -> dict[str, Any]:
    matches = [dict(row) for row in rows if _normalize_text(row.get(key_name)) == _normalize_text(key_value)]
    if not matches:
        return {}
    matches.sort(key=lambda row: (_normalize_text(row.get(order_field)), _normalize_text(row.get("certification_id")), _normalize_text(row.get("alignment_certification_id"))))
    return matches[-1]


def _coverage_status_for_asset(asset: Mapping[str, Any], certification_row: Mapping[str, Any], lifecycle_row: Mapping[str, Any]) -> dict[str, Any]:
    required_components = _normalize_components(asset.get("required_components"))
    support_components = _normalize_components(asset.get("supporting_components"))
    provider_role = _normalize_text(certification_row.get("provider"), "")
    cert_status = _normalize_text(certification_row.get("certification_status"), "missing")
    lifecycle_state = _normalize_text(lifecycle_row.get("lifecycle_state"), "discovered")
    certification_score = _normalize_float(certification_row.get("certification_score"))
    quality_score = _normalize_float(certification_row.get("quality_score"))
    completed = cert_status == "certified"
    if completed and provider_role in _LOCAL_FIXTURE_ROLES:
        readiness_state = "connector_upgrade_required"
        missing_components = ["canonical_production_connector"]
    elif completed:
        readiness_state = "ready"
        missing_components = []
    elif cert_status in {"validated", "partially_certified"} or lifecycle_state in {"source_identified", "connector_mapped", "raw_acquired", "integrity_verified", "normalized"}:
        readiness_state = "partial"
        missing_components = list(required_components)
    elif cert_status == "rejected":
        readiness_state = "blocked"
        missing_components = list(required_components)
    else:
        readiness_state = "missing"
        missing_components = list(required_components)
    completion_percentage = round(certification_score * 100.0, 2) if completed else round(max(certification_score, 0.0) * 100.0, 2)
    if not certification_row:
        completion_percentage = 0.0
    certification_quality = round(max(quality_score, certification_score) * 100.0, 2) if certification_row else 0.0
    if readiness_state == "connector_upgrade_required":
        certification_quality = max(certification_quality, 92.0)
    if readiness_state == "missing" and not certification_row:
        certification_quality = 0.0
    return {
        "bundle_role": _normalize_text(asset.get("bundle_role"), "supporting_context"),
        "required_components": list(required_components),
        "supporting_components": list(support_components),
        "missing_components": missing_components,
        "certification_state": cert_status,
        "lifecycle_state": lifecycle_state,
        "readiness_state": readiness_state,
        "completion_percentage": completion_percentage,
        "quality_score": certification_quality,
        "current_source_role": provider_role,
        "certification_score": round(certification_score * 100.0, 2),
        "source_name": _normalize_text(certification_row.get("source"), "missing"),
        "provider": _normalize_text(certification_row.get("provider"), ""),
    }


def _build_nfl_asset_blueprints(profile_id: str) -> list[dict[str, Any]]:
    profile_fields = _asset_profile_fields(profile_id)
    if profile_id != DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID:
        return []

    def asset(
        *,
        research_asset_id: str,
        research_asset_name: str,
        asset_category: str,
        asset_type: str,
        bundle_role: str,
        required_components: Sequence[str],
        supporting_components: Sequence[str] = (),
        required_inputs: Sequence[str] = (),
        provider_candidates: Mapping[str, Mapping[str, Any]] | None = None,
        notes: Sequence[str] = (),
        minimum_schema: bool = False,
        future_asset: bool = False,
    ) -> dict[str, Any]:
        return {
            "research_asset_id": research_asset_id,
            "research_asset_name": research_asset_name,
            "asset_category": asset_category,
            "asset_type": asset_type,
            "bundle_role": bundle_role,
            "required_components": _normalize_components(required_components),
            "supporting_components": _normalize_components(supporting_components),
            "required_inputs": _normalize_items(required_inputs),
            "provider_candidates": {
                provider_id: {
                    "provider_role": _normalize_text(candidate.get("provider_role"), "primary_acquisition"),
                    "coverage_components": _normalize_components(candidate.get("coverage_components")),
                    "notes": _normalize_text(candidate.get("notes")),
                    "source_aliases": _normalize_items(candidate.get("source_aliases")),
                }
                for provider_id, candidate in dict(provider_candidates or {}).items()
            },
            "notes": list(notes),
            "minimum_schema": bool(minimum_schema),
            "future_asset": bool(future_asset),
            **profile_fields,
        }

    return [
        asset(
            research_asset_id="dataset.nfl.games",
            research_asset_name="NFL Games",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="minimum_schema",
            required_components=(
                "game_identity",
                "season_week",
                "home_away_teams",
                "event_start_time",
                "venue",
                "source_metadata",
                "lineage",
                "point_in_time_alignment",
            ),
            supporting_components=("timezone", "neutral_site", "game_status"),
            required_inputs=("schedule", "team_stats", "final_results", "stable_event_id"),
            provider_candidates={
                "nflverse": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("game_identity", "season_week", "home_away_teams", "event_start_time", "venue", "source_metadata", "lineage", "point_in_time_alignment", "timezone", "neutral_site", "game_status"),
                    "notes": "Canonical open NFL schedule/results dataset family.",
                    "source_aliases": ("nflverse", "nflverse_schedules_results"),
                },
                "nflreadr": {
                    "provider_role": "verification_source",
                    "coverage_components": ("game_identity", "season_week", "home_away_teams", "event_start_time", "venue", "source_metadata", "lineage", "point_in_time_alignment"),
                    "notes": "Open NFL schedule verification lane.",
                    "source_aliases": ("nflreadr",),
                },
                "nflfastr": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("game_identity", "season_week", "home_away_teams", "event_start_time", "source_metadata", "lineage"),
                    "notes": "Historical NFL schedule fallback lane.",
                    "source_aliases": ("nflfastr",),
                },
                "manual_schedule_import": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("game_identity", "season_week", "home_away_teams", "event_start_time", "source_metadata", "lineage"),
                    "notes": "Deterministic manual schedule import lane for local certification and audit replay.",
                    "source_aliases": ("manual_schedule_import",),
                },
            },
            notes=(
                "The current certified schedule asset still uses a deterministic local fixture; the planner should upgrade it to the canonical open schedule connector.",
                "This asset also covers the event backbone used by later markets and research assets.",
            ),
            minimum_schema=True,
        ),
        asset(
            research_asset_id="dataset.sports.nfl.schedule",
            research_asset_name="NFL Schedule",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="minimum_schema",
            required_components=(
                "schedule_rows",
                "event_identifiers",
                "home_away_teams",
                "venue",
                "event_time_alignment",
                "source_metadata",
                "lineage",
            ),
            supporting_components=("timezone", "neutral_site", "game_status"),
            required_inputs=("schedule", "event_id", "timestamp"),
            provider_candidates={
                "nflverse": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("schedule_rows", "event_identifiers", "home_away_teams", "venue", "event_time_alignment", "source_metadata", "lineage", "timezone", "neutral_site", "game_status"),
                    "notes": "Primary open NFL schedule source.",
                    "source_aliases": ("nflverse", "nflverse_schedules_results"),
                },
                "nflreadr": {
                    "provider_role": "verification_source",
                    "coverage_components": ("schedule_rows", "event_identifiers", "home_away_teams", "venue", "event_time_alignment", "source_metadata", "lineage"),
                    "notes": "Verification lane for the first production connector.",
                    "source_aliases": ("nflreadr",),
                },
                "nflfastr": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("schedule_rows", "event_identifiers", "home_away_teams", "event_time_alignment", "source_metadata", "lineage"),
                    "notes": "Fallback open NFL schedule lane.",
                    "source_aliases": ("nflfastr",),
                },
                "manual_schedule_import": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("schedule_rows", "event_identifiers", "home_away_teams", "venue", "event_time_alignment", "source_metadata", "lineage"),
                    "notes": "Manual import fallback if the open connector path is unavailable.",
                    "source_aliases": ("manual_schedule_import",),
                },
            },
            notes=(
                "This is the first production connector target because it replaces the current deterministic fixture without changing the event-centric model.",
                "The same provider family also covers the NFL games backbone used by later joins.",
            ),
            minimum_schema=True,
        ),
        asset(
            research_asset_id="dataset.sports.nfl.results",
            research_asset_name="NFL Results",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="minimum_schema",
            required_components=("final_score", "winner", "settlement_status", "result_timestamp", "source_metadata", "lineage"),
            supporting_components=("margin", "overtime", "venue", "event_time_alignment"),
            required_inputs=("final_results", "stable_event_id"),
            provider_candidates={
                "nflverse": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("final_score", "winner", "settlement_status", "result_timestamp", "source_metadata", "lineage", "margin", "overtime"),
                    "notes": "Open NFL results and final scoreboard coverage.",
                    "source_aliases": ("nflverse", "nflverse_schedules_results"),
                },
                "nflfastr": {
                    "provider_role": "verification_source",
                    "coverage_components": ("final_score", "winner", "settlement_status", "result_timestamp", "source_metadata", "lineage"),
                    "notes": "Historical open results verification lane.",
                    "source_aliases": ("nflfastr",),
                },
                "nflreadr": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("final_score", "winner", "settlement_status", "result_timestamp", "source_metadata", "lineage"),
                    "notes": "Open results fallback lane.",
                    "source_aliases": ("nflreadr",),
                },
                "manual_schedule_import": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("final_score", "winner", "settlement_status", "result_timestamp", "source_metadata", "lineage"),
                    "notes": "Manual result imports for audit and correction workflows.",
                    "source_aliases": ("manual_schedule_import", "manual_import"),
                },
            },
            notes=("Results reuse the certified schedule identity and the existing NFL schedule/results connector family.",),
            minimum_schema=True,
        ),
        asset(
            research_asset_id="dataset.nfl.odds_snapshots",
            research_asset_name="NFL Odds Snapshots",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="minimum_schema",
            required_components=("bookmaker", "market_type", "selection", "line", "odds", "snapshot_time", "source_metadata", "lineage"),
            supporting_components=("opening_line", "closing_line", "price_type"),
            required_inputs=("event_id", "market_type", "selection", "odds", "line", "timestamp", "final_results"),
            provider_candidates={
                "the_odds_api": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("bookmaker", "market_type", "selection", "line", "odds", "snapshot_time", "source_metadata", "lineage", "opening_line", "closing_line"),
                    "notes": "Canonical odds API candidate in the source registry.",
                    "source_aliases": ("the_odds_api", "the_odds_api_market"),
                },
                "sportsgameodds": {
                    "provider_role": "verification_source",
                    "coverage_components": ("bookmaker", "market_type", "selection", "line", "odds", "snapshot_time", "source_metadata", "lineage"),
                    "notes": "Odds verification lane.",
                    "source_aliases": ("sportsgameodds",),
                },
                "odds_api_io": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("bookmaker", "market_type", "selection", "line", "odds", "snapshot_time", "source_metadata", "lineage"),
                    "notes": "Odds fallback lane.",
                    "source_aliases": ("odds_api_io",),
                },
                "oddsmagnet": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("bookmaker", "market_type", "selection", "line", "odds", "snapshot_time", "source_metadata", "lineage"),
                    "notes": "Odds enrichment lane.",
                    "source_aliases": ("oddsmagnet",),
                },
                "the_odds_api_market": {
                    "provider_role": "future_enrichment",
                    "coverage_components": ("bookmaker", "market_type", "selection", "line", "odds", "snapshot_time", "source_metadata", "lineage"),
                    "notes": "Documented market archive candidate.",
                    "source_aliases": ("the_odds_api_market",),
                },
            },
            notes=("Betting/odds coverage remains point-in-time sensitive and must remain snapshot-based.",),
            minimum_schema=True,
        ),
        asset(
            research_asset_id="dataset.nfl.weather_snapshots",
            research_asset_name="NFL Weather Snapshots",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="minimum_schema",
            required_components=("location", "snapshot_time", "temperature", "wind", "precipitation", "source_metadata", "lineage"),
            supporting_components=("forecast_time", "observation_time", "roof_status"),
            required_inputs=("event_id", "location", "timestamp", "temperature", "wind", "precipitation"),
            provider_candidates={
                "open_meteo": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("location", "snapshot_time", "temperature", "wind", "precipitation", "source_metadata", "lineage", "forecast_time"),
                    "notes": "Open weather source that keeps the data local and reproducible.",
                    "source_aliases": ("open_meteo", "open_meteo_forecast", "open_meteo_historical"),
                },
                "national_weather_service": {
                    "provider_role": "verification_source",
                    "coverage_components": ("location", "snapshot_time", "temperature", "wind", "precipitation", "source_metadata", "lineage"),
                    "notes": "US weather verification lane.",
                    "source_aliases": ("national_weather_service",),
                },
                "noaa_public_datasets": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("location", "snapshot_time", "temperature", "wind", "precipitation", "source_metadata", "lineage"),
                    "notes": "Historical weather fallback lane.",
                    "source_aliases": ("noaa_public_datasets",),
                },
                "weatherapi": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("location", "snapshot_time", "temperature", "wind", "precipitation", "source_metadata", "lineage"),
                    "notes": "Free-key weather enrichment lane.",
                    "source_aliases": ("weatherapi",),
                },
                "weatherstack": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("location", "snapshot_time", "temperature", "wind", "precipitation", "source_metadata", "lineage"),
                    "notes": "Weather enrichment lane that remains secondary to open providers.",
                    "source_aliases": ("weatherstack",),
                },
                "open_meteo_stadium_weather": {
                    "provider_role": "future_enrichment",
                    "coverage_components": ("location", "snapshot_time", "temperature", "wind", "precipitation", "source_metadata", "lineage"),
                    "notes": "Documented stadium-coordinate alias candidate.",
                    "source_aliases": ("open_meteo_stadium_weather",),
                },
            },
            notes=("Weather must remain snapshot-based so future models never leak post-event information.",),
            minimum_schema=True,
        ),
        asset(
            research_asset_id="dataset.nfl.team_stats_snapshots",
            research_asset_name="NFL Team Statistics Snapshots",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="minimum_schema",
            required_components=("team_week", "efficiency_metrics", "pace_metrics", "source_metadata", "lineage"),
            supporting_components=("offense", "defense", "scoring_profile"),
            required_inputs=("schedule", "team_stats", "final_results", "stable_event_id"),
            provider_candidates={
                "nflverse": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("team_week", "efficiency_metrics", "pace_metrics", "source_metadata", "lineage", "offense", "defense", "scoring_profile"),
                    "notes": "Canonical weekly team stats lane.",
                    "source_aliases": ("nflverse", "nflverse_team_stats"),
                },
                "nflfastr": {
                    "provider_role": "verification_source",
                    "coverage_components": ("team_week", "efficiency_metrics", "pace_metrics", "source_metadata", "lineage"),
                    "notes": "Weekly team stats verification lane.",
                    "source_aliases": ("nflfastr",),
                },
                "nflreadr": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("team_week", "efficiency_metrics", "pace_metrics", "source_metadata", "lineage"),
                    "notes": "Weekly team stats fallback lane.",
                    "source_aliases": ("nflreadr",),
                },
            },
            notes=("Team statistics are the first reusable efficiency layer after the schedule and results facts are certified.",),
            minimum_schema=True,
        ),
        asset(
            research_asset_id="dataset.nfl.injury_snapshots",
            research_asset_name="NFL Injury Snapshots",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="future_enrichment",
            required_components=("player_status", "report_time", "team", "player", "source_metadata", "lineage"),
            supporting_components=("injury_status", "availability_status", "practice_participation"),
            required_inputs=("player_stats", "team_stats", "final_results"),
            provider_candidates={
                "nflverse_injuries": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("player_status", "report_time", "team", "player", "source_metadata", "lineage", "injury_status", "availability_status"),
                    "notes": "Open NFL injuries lane from the data registry and the canonical fixture-backed report-time-safe acquisition path.",
                    "source_aliases": ("nflverse_injuries",),
                },
                "manual_import": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("player_status", "report_time", "team", "player", "source_metadata", "lineage", "injury_status"),
                    "notes": "Manual evidence fallback when timing, terms review, or provenance requires a reviewed local import.",
                    "source_aliases": ("manual_import",),
                },
                "official_team_reports": {
                    "provider_role": "verification_source",
                    "coverage_components": ("player_status", "report_time", "team", "player", "source_metadata", "lineage", "injury_status"),
                    "notes": "Documentation-only official injury reports candidate.",
                    "source_aliases": ("official_team_reports",),
                },
                "official_team_press_releases": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("player_status", "report_time", "team", "player", "source_metadata", "lineage"),
                    "notes": "Official team press-release backup lane.",
                    "source_aliases": ("official_team_press_releases",),
                },
                "official_nfl_staff_or_news_pages": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("player_status", "report_time", "team", "player", "source_metadata", "lineage"),
                    "notes": "Official NFL staff/news enrichment lane.",
                    "source_aliases": ("official_nfl_staff_or_news_pages",),
                },
            },
            notes=("Injury timing is a leakage-sensitive context asset; the open nflverse path and the manual evidence fallback must both preserve report timestamps and provenance.",),
            future_asset=True,
        ),
        asset(
            research_asset_id="dataset.nfl.officials",
            research_asset_name="NFL Officials",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="future_enrichment",
            required_components=("crew_assignment", "assignment_time", "game_id", "source_metadata", "lineage"),
            supporting_components=("referee", "umpire", "line_judge", "down_judge"),
            required_inputs=("event_id", "timestamp", "source_context", "stable_join_key"),
            provider_candidates={
                "official_gamebook_records": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("crew_assignment", "assignment_time", "game_id", "source_metadata", "lineage", "referee", "umpire", "line_judge", "down_judge"),
                    "notes": "Documented gamebook/assignment placeholder from the discovery inventory.",
                    "source_aliases": ("official_gamebook_records",),
                },
                "manual_import": {
                    "provider_role": "verification_source",
                    "coverage_components": ("crew_assignment", "assignment_time", "game_id", "source_metadata", "lineage"),
                    "notes": "Manual import fallback for officials assignments.",
                    "source_aliases": ("manual_import",),
                },
            },
            notes=("Officials remain a future enrichment asset with explicit time alignment requirements.",),
            future_asset=True,
        ),
        asset(
            research_asset_id="dataset.nfl.coaching",
            research_asset_name="NFL Coaching",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="future_enrichment",
            required_components=("head_coach", "coordinator_roles", "effective_date", "source_metadata", "lineage"),
            supporting_components=("offensive_coordinator", "defensive_coordinator", "special_teams_coordinator", "staff_role"),
            required_inputs=("team", "season", "head_coach", "offensive_coordinator", "defensive_coordinator", "special_teams_coordinator"),
            provider_candidates={
                "wikidata_coaching_seed": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("head_coach", "coordinator_roles", "effective_date", "source_metadata", "lineage", "staff_role"),
                    "notes": "Open structured coaching seed lane.",
                    "source_aliases": ("wikidata_coaching_seed",),
                },
                "wikipedia_coaching_seed": {
                    "provider_role": "verification_source",
                    "coverage_components": ("head_coach", "coordinator_roles", "effective_date", "source_metadata", "lineage"),
                    "notes": "Wikipedia coaching seed lane.",
                    "source_aliases": ("wikipedia_coaching_seed", "wikipedia_coaching_tables"),
                },
                "open_github_nfl_coaches_dataset": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("head_coach", "coordinator_roles", "effective_date", "source_metadata", "lineage"),
                    "notes": "License-gated coaching dataset candidate from the discovery inventory.",
                    "source_aliases": ("open_github_nfl_coaches_dataset",),
                },
                "official_team_staff_pages": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("head_coach", "coordinator_roles", "effective_date", "source_metadata", "lineage"),
                    "notes": "Official staff-page enrichment lane subject to terms review.",
                    "source_aliases": ("official_team_staff_pages",),
                },
                "official_team_press_releases": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("head_coach", "coordinator_roles", "effective_date", "source_metadata", "lineage"),
                    "notes": "Official press-release enrichment lane.",
                    "source_aliases": ("official_team_press_releases",),
                },
                "official_nfl_staff_or_news_pages": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("head_coach", "coordinator_roles", "effective_date", "source_metadata", "lineage"),
                    "notes": "Official NFL news/staff enrichment lane.",
                    "source_aliases": ("official_nfl_staff_or_news_pages",),
                },
                "pro_football_reference_web": {
                    "provider_role": "future_enrichment",
                    "coverage_components": ("head_coach", "coordinator_roles", "effective_date", "source_metadata", "lineage"),
                    "notes": "Blocked terms-sensitive reference lane recorded in the discovery audit.",
                    "source_aliases": ("pro_football_reference_web",),
                },
            },
            notes=("Coaching is future enrichment, but the planner must already know which structured open lanes can eventually supply it.",),
            future_asset=True,
        ),
        asset(
            research_asset_id="dataset.nfl.player_statistics",
            research_asset_name="NFL Player Statistics",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="future_enrichment",
            required_components=("player_id", "position", "player_week_stats", "source_metadata", "lineage"),
            supporting_components=("snap_counts", "rosters", "depth_chart", "participation"),
            required_inputs=("schedule", "team_stats", "player_stats", "final_results", "stable_event_id"),
            provider_candidates={
                "nflverse_weekly_player_stats": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("player_id", "position", "player_week_stats", "source_metadata", "lineage", "snap_counts", "participation"),
                    "notes": "Primary NFL player stats lane from the open data source registry.",
                    "source_aliases": ("nflverse_weekly_player_stats",),
                },
                "nflfastr": {
                    "provider_role": "verification_source",
                    "coverage_components": ("player_id", "position", "player_week_stats", "source_metadata", "lineage"),
                    "notes": "Player stats verification lane.",
                    "source_aliases": ("nflfastr",),
                },
                "nflreadr": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("player_id", "position", "player_week_stats", "source_metadata", "lineage"),
                    "notes": "Player stats fallback lane.",
                    "source_aliases": ("nflreadr",),
                },
                "nflverse_rosters": {
                    "provider_role": "supporting_source",
                    "coverage_components": ("player_id", "position", "rosters", "source_metadata", "lineage"),
                    "notes": "Roster continuity support lane.",
                    "source_aliases": ("nflverse_rosters", "nflverse_weekly_rosters"),
                },
                "nflverse_snap_counts": {
                    "provider_role": "supporting_source",
                    "coverage_components": ("player_id", "snap_counts", "source_metadata", "lineage"),
                    "notes": "Snap-count support lane.",
                    "source_aliases": ("nflverse_snap_counts",),
                },
                "nflverse_participation": {
                    "provider_role": "supporting_source",
                    "coverage_components": ("player_id", "participation", "source_metadata", "lineage"),
                    "notes": "Participation support lane.",
                    "source_aliases": ("nflverse_participation",),
                },
                "nflverse_depth_charts": {
                    "provider_role": "supporting_source",
                    "coverage_components": ("player_id", "depth_chart", "source_metadata", "lineage"),
                    "notes": "Depth-chart support lane.",
                    "source_aliases": ("nflverse_depth_charts",),
                },
            },
            notes=("Player statistics remain future enrichment until the minimum schedule/results/odds/weather/team-stat slice is proven reusable.",),
            future_asset=True,
        ),
        asset(
            research_asset_id="dataset.nfl.opening_odds",
            research_asset_name="NFL Opening Odds",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="future_enrichment",
            required_components=("bookmaker", "open_line", "open_odds", "open_snapshot_time", "source_metadata", "lineage"),
            supporting_components=("market_type", "selection", "price_type"),
            required_inputs=("event_id", "market_type", "selection", "odds", "line", "timestamp", "final_results"),
            provider_candidates={
                "the_odds_api": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("bookmaker", "open_line", "open_odds", "open_snapshot_time", "source_metadata", "lineage", "market_type", "selection"),
                    "notes": "Odds API candidate for opening markets.",
                    "source_aliases": ("the_odds_api", "the_odds_api_market"),
                },
                "sportsgameodds": {
                    "provider_role": "verification_source",
                    "coverage_components": ("bookmaker", "open_line", "open_odds", "open_snapshot_time", "source_metadata", "lineage"),
                    "notes": "Opening odds verification lane.",
                    "source_aliases": ("sportsgameodds",),
                },
                "odds_api_io": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("bookmaker", "open_line", "open_odds", "open_snapshot_time", "source_metadata", "lineage"),
                    "notes": "Opening odds fallback lane.",
                    "source_aliases": ("odds_api_io",),
                },
                "oddsmagnet": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("bookmaker", "open_line", "open_odds", "open_snapshot_time", "source_metadata", "lineage"),
                    "notes": "Opening odds enrichment lane.",
                    "source_aliases": ("oddsmagnet",),
                },
            },
            notes=("Opening odds are future enrichment and must stay point-in-time safe.",),
            future_asset=True,
        ),
        asset(
            research_asset_id="dataset.nfl.closing_odds",
            research_asset_name="NFL Closing Odds",
            asset_category="dataset",
            asset_type="table_snapshot",
            bundle_role="future_enrichment",
            required_components=("bookmaker", "closing_line", "closing_odds", "closing_snapshot_time", "source_metadata", "lineage"),
            supporting_components=("market_type", "selection", "price_type"),
            required_inputs=("event_id", "market_type", "selection", "odds", "line", "timestamp", "final_results"),
            provider_candidates={
                "the_odds_api": {
                    "provider_role": "primary_acquisition",
                    "coverage_components": ("bookmaker", "closing_line", "closing_odds", "closing_snapshot_time", "source_metadata", "lineage", "market_type", "selection"),
                    "notes": "Odds API candidate for closing markets.",
                    "source_aliases": ("the_odds_api", "the_odds_api_market"),
                },
                "sportsgameodds": {
                    "provider_role": "verification_source",
                    "coverage_components": ("bookmaker", "closing_line", "closing_odds", "closing_snapshot_time", "source_metadata", "lineage"),
                    "notes": "Closing odds verification lane.",
                    "source_aliases": ("sportsgameodds",),
                },
                "odds_api_io": {
                    "provider_role": "fallback_source",
                    "coverage_components": ("bookmaker", "closing_line", "closing_odds", "closing_snapshot_time", "source_metadata", "lineage"),
                    "notes": "Closing odds fallback lane.",
                    "source_aliases": ("odds_api_io",),
                },
                "oddsmagnet": {
                    "provider_role": "enrichment_source",
                    "coverage_components": ("bookmaker", "closing_line", "closing_odds", "closing_snapshot_time", "source_metadata", "lineage"),
                    "notes": "Closing odds enrichment lane.",
                    "source_aliases": ("oddsmagnet",),
                },
            },
            notes=("Closing odds remain future enrichment and must be guarded for decision-time leakage.",),
            future_asset=True,
        ),
    ]


def _build_supplemental_provider_sources() -> list[dict[str, Any]]:
    return [
        {
            "source_id": "official_gamebook_records",
            "source_name": "Official gamebook records",
            "source_family": "official_gamebook_records",
            "source_access_type": "manual_import",
            "source_category": "sports",
            "source_kind": "manual_csv",
            "data_category": "officials",
            "current_phase_allowed": True,
            "future_source_candidate": True,
            "approval_status": "approved_manual_import",
            "terms_review_status": "research_required",
            "notes": "Documented discovery placeholder from the NFL provider inventory.",
        },
        {
            "source_id": "official_team_reports",
            "source_name": "Official team injury reports",
            "source_family": "official_team_reports",
            "source_access_type": "manual_import",
            "source_category": "sports",
            "source_kind": "manual_csv",
            "data_category": "injuries",
            "current_phase_allowed": True,
            "future_source_candidate": True,
            "approval_status": "approved_manual_import",
            "terms_review_status": "research_required",
            "notes": "Documented discovery placeholder for the injury lane.",
        },
        {
            "source_id": "open_meteo_stadium_weather",
            "source_name": "Open-Meteo stadium weather",
            "source_family": "open_meteo_stadium_weather",
            "source_access_type": "rest_api",
            "source_category": "weather",
            "source_kind": "rest_api",
            "data_category": "weather",
            "current_phase_allowed": True,
            "future_source_candidate": True,
            "approval_status": "approved_open_metadata",
            "terms_review_status": "reviewed_open_allowed",
            "notes": "Discovery alias for stadium-coordinate weather coverage.",
        },
    ]


@lru_cache(maxsize=1)
def _source_catalog() -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    nfl_registry_sources = list(build_registry(module="americanfootball_nfl").get("sources", []))
    cross_cutting_sources = [source for source in build_registry().get("sources", []) if _source_identifier(source) in _CROSS_CUTTING_SOURCE_IDS]
    for source in nfl_registry_sources + cross_cutting_sources:
        source_id = _source_identifier(source)
        if not source_id:
            continue
        catalog[source_id] = _merge_non_empty(catalog.get(source_id, {}), dict(source))
    for source in nfl_open_data_sources():
        source_id = _source_identifier(source)
        if not source_id:
            continue
        catalog[source_id] = _merge_non_empty(catalog.get(source_id, {}), dict(source))
    for source in nfl_coaching_sources():
        source_id = _source_identifier(source)
        if not source_id:
            continue
        catalog[source_id] = _merge_non_empty(catalog.get(source_id, {}), dict(source))
    for source in nfl_candidate_sources():
        source_id = _source_identifier(source)
        if not source_id:
            continue
        catalog[source_id] = _merge_non_empty(catalog.get(source_id, {}), dict(source))
    for source in _build_supplemental_provider_sources():
        source_id = _source_identifier(source)
        if not source_id:
            continue
        catalog[source_id] = _merge_non_empty(catalog.get(source_id, {}), source)
    return catalog


@lru_cache(maxsize=8)
def _nfl_asset_blueprints(profile_id: str) -> tuple[dict[str, Any], ...]:
    return tuple(_build_nfl_asset_blueprints(profile_id))


def _certification_runtime(store: LocalStorageEngine, storage_path: str | Path, backend: str) -> HistoricalResearchAssetCertificationRuntime:
    return HistoricalResearchAssetCertificationRuntime(
        storage_path=storage_path,
        backend=backend,
        store=store,
    )


def _lifecycle_runtime(store: LocalStorageEngine, storage_path: str | Path, backend: str) -> ResearchAssetLifecycleRuntime:
    return ResearchAssetLifecycleRuntime(
        storage_path=storage_path,
        backend=backend,
        store=store,
    )


def _latest_grouped_rows(rows: Sequence[Mapping[str, Any]], *, key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        identifier = _normalize_text(row.get(key))
        if identifier:
            grouped[identifier].append(dict(row))
    latest: dict[str, dict[str, Any]] = {}
    for identifier, items in grouped.items():
        items.sort(key=lambda row: (_normalize_text(row.get("updated_at")), _normalize_text(row.get("certification_id")), _normalize_text(row.get("alignment_certification_id"))))
        latest[identifier] = items[-1]
    return latest


def _provider_bundle_for_asset(asset: Mapping[str, Any], provider_registry: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    candidate_rows: list[dict[str, Any]] = []
    for provider_id, candidate in dict(asset.get("provider_candidates") or {}).items():
        provider_source = dict(provider_registry.get(provider_id, {}))
        if not provider_source:
            provider_source = {
                "source_id": provider_id,
                "source_name": candidate.get("notes") or provider_id,
                "source_family": provider_id,
                "source_access_type": "future_only" if candidate.get("provider_role") == "future_enrichment" else "manual_import",
                "approval_status": "candidate",
                "current_phase_allowed": False if candidate.get("provider_role") == "future_enrichment" else True,
            }
        provider_score = _build_provider_score(
            provider_source,
            coverage_components=candidate.get("coverage_components", ()),
            required_components=asset.get("required_components", ()),
            required_inputs=asset.get("required_inputs", ()),
        )
        candidate_rows.append(
            {
                "provider_id": provider_id,
                "provider_name": _source_name(provider_source),
                "provider_role": _normalize_text(candidate.get("provider_role"), provider_score["provider_role"]),
                "selection_score": provider_score["selection_score"],
                "coverage_score": provider_score["coverage_score"],
                "historical_depth_score": provider_score["historical_depth_score"],
                "point_in_time_safety_score": provider_score["point_in_time_safety_score"],
                "licensing_score": provider_score["licensing_score"],
                "reliability_score": provider_score["reliability_score"],
                "cost_score": provider_score["cost_score"],
                "update_frequency_score": provider_score["update_frequency_score"],
                "reproducibility_score": provider_score["reproducibility_score"],
                "certification_suitability_score": provider_score["certification_suitability_score"],
                "quality_tier": provider_score["quality_tier"],
                "source_access_type": provider_score["source_access_type"],
                "current_phase_allowed": provider_score["current_phase_allowed"],
                "approval_status": provider_score["approval_status"],
                "coverage_components": list(_normalize_components(candidate.get("coverage_components"))),
                "source_aliases": list(_normalize_items(candidate.get("source_aliases"))),
                "notes": _normalize_text(candidate.get("notes")),
                "source_quality_snapshot": provider_score["source_quality_snapshot"],
            }
        )
    candidate_rows.sort(key=lambda row: (-float(row.get("selection_score") or 0.0), _normalize_text(row.get("provider_id"))))
    primary = candidate_rows[0] if candidate_rows else {}
    verification = candidate_rows[1] if len(candidate_rows) > 1 else {}
    fallback = candidate_rows[2] if len(candidate_rows) > 2 else {}
    enrichment = candidate_rows[3:] if len(candidate_rows) > 3 else []
    selected_provider_ids = [row["provider_id"] for row in candidate_rows[:4] if row.get("provider_id")]
    coverage_components = sorted({component for row in candidate_rows for component in row.get("coverage_components", [])})
    provider_bundle = {
        "selected_provider_ids": selected_provider_ids,
        "primary_provider_id": primary.get("provider_id", ""),
        "verification_provider_id": verification.get("provider_id", ""),
        "fallback_provider_id": fallback.get("provider_id", ""),
        "enrichment_provider_ids": [row.get("provider_id", "") for row in enrichment if row.get("provider_id")],
        "provider_roles": {
            "primary": primary.get("provider_role", ""),
            "verification": verification.get("provider_role", ""),
            "fallback": fallback.get("provider_role", ""),
            "enrichment": [row.get("provider_role", "") for row in enrichment if row.get("provider_role")],
        },
        "selection_score": round(sum(float(row.get("selection_score") or 0.0) for row in candidate_rows[:4]) / max(len(candidate_rows[:4]), 1), 2) if candidate_rows else 0.0,
        "coverage_components": coverage_components,
        "provider_candidates": candidate_rows,
    }
    return provider_bundle


def _build_research_asset_coverage_row(
    asset: Mapping[str, Any],
    *,
    certification_row: Mapping[str, Any],
    lifecycle_row: Mapping[str, Any],
    provider_registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    provider_bundle = _provider_bundle_for_asset(asset, provider_registry)
    asset_state = _coverage_status_for_asset(asset, certification_row, lifecycle_row)
    certified = _normalize_text(certification_row.get("certification_status")) == "certified"
    completion_percentage = asset_state["completion_percentage"]
    if not certification_row:
        completion_percentage = 0.0
    if certified and asset_state["readiness_state"] == "connector_upgrade_required":
        quality_score = max(asset_state["quality_score"], provider_bundle["selection_score"])
    elif certified:
        quality_score = max(asset_state["quality_score"], provider_bundle["selection_score"])
    else:
        quality_score = provider_bundle["selection_score"]
    return {
        "research_asset_id": asset["research_asset_id"],
        "research_asset_name": asset["research_asset_name"],
        "asset_category": asset["asset_category"],
        "asset_type": asset["asset_type"],
        "bundle_role": asset_state["bundle_role"],
        "market_profile": asset.get("market_profile", DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID),
        "market_family": asset.get("market_family", "sports"),
        "minimum_schema": bool(asset.get("minimum_schema", False)),
        "future_asset": bool(asset.get("future_asset", False)),
        "required_components": asset_state["required_components"],
        "supporting_components": asset_state["supporting_components"],
        "missing_components": asset_state["missing_components"],
        "certification_state": asset_state["certification_state"],
        "lifecycle_state": asset_state["lifecycle_state"],
        "readiness_state": asset_state["readiness_state"],
        "completion_percentage": round(completion_percentage, 2),
        "quality_score": round(quality_score, 2),
        "current_source_role": asset_state["current_source_role"],
        "current_source_name": asset_state["source_name"],
        "current_provider": asset_state["provider"],
        "recommended_primary_provider": provider_bundle["primary_provider_id"],
        "recommended_verification_provider": provider_bundle["verification_provider_id"],
        "recommended_fallback_provider": provider_bundle["fallback_provider_id"],
        "recommended_enrichment_providers": provider_bundle["enrichment_provider_ids"],
        "provider_candidates": provider_bundle["selected_provider_ids"] or [row["provider_id"] for row in provider_bundle["provider_candidates"]],
        "provider_bundle": provider_bundle,
        "provider_selection_score": provider_bundle["selection_score"],
        "coverage_gap_status": "connector_upgrade_required" if asset_state["readiness_state"] == "connector_upgrade_required" else "missing" if asset_state["readiness_state"] == "missing" else "covered",
        "notes": list(asset.get("notes") or ()),
    }


def _build_asset_catalog_for_profile(
    *,
    profile_id: str,
    certification_rows: Sequence[Mapping[str, Any]],
    lifecycle_rows: Sequence[Mapping[str, Any]],
    provider_registry: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    assets = []
    cert_index = _latest_grouped_rows(certification_rows, key="research_asset_id")
    lifecycle_index = _latest_grouped_rows(lifecycle_rows, key="asset_id")
    for asset in _nfl_asset_blueprints(profile_id):
        asset_id = _normalize_text(asset.get("research_asset_id"))
        assets.append(
            _build_research_asset_coverage_row(
                asset,
                certification_row=cert_index.get(asset_id, {}),
                lifecycle_row=lifecycle_index.get(asset_id, {}),
                provider_registry=provider_registry,
            )
        )
    return assets


def _build_provider_registry_for_profile(*, profile_id: str, asset_catalog: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    provider_records = []
    for provider_id, source in sorted(_source_catalog().items(), key=lambda item: item[0]):
        provider_record = _build_provider_record(provider_id, source, asset_catalog)
        if provider_record["supported_assets"] or provider_record["future_candidate"]:
            provider_records.append(provider_record)
    provider_records.sort(key=lambda row: (-float(row.get("selection_score") or 0.0), _normalize_text(row.get("provider_id"))))
    return provider_records


def _build_coverage_gap_engine(
    *,
    profile_id: str,
    asset_catalog: Sequence[Mapping[str, Any]],
    provider_registry: Sequence[Mapping[str, Any]],
    certification_rows: Sequence[Mapping[str, Any]],
    lifecycle_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    required_assets = [asset for asset in asset_catalog if bool(asset.get("minimum_schema"))]
    certified_assets = [asset for asset in required_assets if _normalize_text(asset.get("certification_state")) == "certified"]
    connector_upgrade_assets = [asset for asset in required_assets if _normalize_text(asset.get("readiness_state")) == "connector_upgrade_required"]
    missing_assets = [asset for asset in required_assets if _normalize_text(asset.get("readiness_state")) in {"missing", "partial"}]
    future_assets = [asset for asset in asset_catalog if bool(asset.get("future_asset"))]
    completion_percentage = round(100.0 * len(certified_assets) / max(len(required_assets), 1), 2)
    next_acquisition_targets: list[dict[str, Any]] = []
    if connector_upgrade_assets:
        next_acquisition_targets.append(
            {
                "target_type": "connector_upgrade",
                "priority_rank": 0,
                "research_asset_ids": [asset["research_asset_id"] for asset in connector_upgrade_assets],
                "recommended_primary_provider": connector_upgrade_assets[0]["recommended_primary_provider"],
                "recommended_verification_provider": connector_upgrade_assets[0]["recommended_verification_provider"],
                "recommended_fallback_provider": connector_upgrade_assets[0]["recommended_fallback_provider"],
                "provider_bundle": connector_upgrade_assets[0]["provider_bundle"],
                "coverage_before": connector_upgrade_assets[0]["completion_percentage"],
                "coverage_after": 100.0,
                "reason": "replace the deterministic fixture with the canonical production connector and preserve the same event-centric join keys",
            }
        )
    next_acquisition_targets.extend(
        [
            {
                "target_type": "missing_required_asset",
                "priority_rank": len(next_acquisition_targets) + index + 1,
                "research_asset_ids": [asset["research_asset_id"]],
                "recommended_primary_provider": asset["recommended_primary_provider"],
                "recommended_verification_provider": asset["recommended_verification_provider"],
                "recommended_fallback_provider": asset["recommended_fallback_provider"],
                "provider_bundle": asset["provider_bundle"],
                "coverage_before": asset["completion_percentage"],
                "coverage_after": 100.0 if asset["provider_bundle"].get("primary_provider_id") else asset["completion_percentage"],
                "reason": "minimum-schema asset is still missing and must become certified before later markets can depend on it",
            }
            for index, asset in enumerate(missing_assets)
        ]
    )
    future_needs = [
        {
            "target_type": "future_enrichment",
            "priority_rank": len(next_acquisition_targets) + index + 1,
            "research_asset_ids": [asset["research_asset_id"]],
            "recommended_primary_provider": asset["recommended_primary_provider"],
            "recommended_verification_provider": asset["recommended_verification_provider"],
            "recommended_fallback_provider": asset["recommended_fallback_provider"],
            "provider_bundle": asset["provider_bundle"],
            "coverage_before": asset["completion_percentage"],
            "coverage_after": 100.0 if asset["provider_bundle"].get("primary_provider_id") else asset["completion_percentage"],
            "reason": "future enrichment remains documented so the repository already knows where later research assets will come from",
        }
        for index, asset in enumerate(sorted(future_assets, key=lambda row: (-float(row.get("provider_selection_score") or 0.0), _normalize_text(row.get("research_asset_id")))))
    ]
    next_acquisition_targets.extend(future_needs)
    first_production_connector_target = _normalize_text(next_acquisition_targets[0]["research_asset_ids"][0]) if next_acquisition_targets else ""
    return {
        "profile_id": profile_id,
        "required_asset_count": len(required_assets),
        "certified_asset_count": len(certified_assets),
        "connector_upgrade_asset_count": len(connector_upgrade_assets),
        "missing_asset_count": len(missing_assets),
        "future_asset_count": len(future_assets),
        "minimum_schema_completion_percentage": completion_percentage,
        "first_production_connector_target": first_production_connector_target,
        "certified_required_asset_ids": [asset["research_asset_id"] for asset in certified_assets],
        "connector_upgrade_asset_ids": [asset["research_asset_id"] for asset in connector_upgrade_assets],
        "missing_required_asset_ids": [asset["research_asset_id"] for asset in missing_assets],
        "future_asset_ids": [asset["research_asset_id"] for asset in future_assets],
        "next_acquisition_targets": next_acquisition_targets,
        "coverage_summary": {
            "all_assets_total": len(asset_catalog),
            "required_assets_total": len(required_assets),
            "future_assets_total": len(future_assets),
            "certified_assets_total": len(certified_assets),
            "connector_upgrade_assets_total": len(connector_upgrade_assets),
            "missing_required_assets_total": len(missing_assets),
        },
        "notes": [
            "Coverage is asset-first: the planner tracks what is certified, what is missing, and which provider bundle best closes each gap.",
            "The first production connector target remains the NFL schedule asset so the fixture-backed path can be replaced by the canonical open provider bundle.",
        ],
    }


def _build_worldview_query_surface(*, profile_id: str, asset_catalog: Sequence[Mapping[str, Any]], coverage_gap_engine: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "profile_id": profile_id,
        "query_surface": [
            "What assets are missing?",
            "Which datasets are certified?",
            "Which providers remain unused?",
            "What evidence supports this feature?",
            "Why is this dataset blocked?",
            "What certification failed?",
            "Which season has incomplete coverage?",
            "Which market is production ready?",
            "What prevents NFL Week 3 from backtesting?",
            "What connector would close this gap?",
        ],
        "supported_questions": [
            {
                "question": "Which research assets are certified and which are missing?",
                "evidence": "coverage_gap_engine -> certified_required_asset_ids / missing_required_asset_ids",
            },
            {
                "question": "What should be acquired next?",
                "evidence": "coverage_gap_engine -> next_acquisition_targets",
            },
            {
                "question": "Which providers are unused?",
                "evidence": "provider_coverage_registry -> supported_assets / future_candidate",
            },
            {
                "question": "What blocks backtesting readiness?",
                "evidence": "asset readiness_state, lifecycle_state, and certification_state",
            },
        ],
        "evidence_packages": [
            "certification rows",
            "lifecycle rows",
            "provider coverage registry",
            "coverage gap engine",
            "acquisition plans",
            "source discovery records",
        ],
        "worldview_permissions": [
            "query certified assets",
            "query missing assets",
            "query certification failures",
            "query provider selection plans",
            "query readiness states",
        ],
        "notes": [
            "Worldview remains a research scientist and only queries certified evidence from the repository laboratory.",
            "The query surface is documentation and runtime metadata only; no AI behavior is implemented here.",
        ],
        "asset_catalog_size": len(asset_catalog),
        "coverage_completion_percentage": coverage_gap_engine.get("minimum_schema_completion_percentage", 0.0),
    }


@dataclass(slots=True)
class ResearchAssetCoveragePlannerRuntime:
    storage_path: Path
    backend: str = "sqlite"
    dataset_owner: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_OWNER
    store: LocalStorageEngine | None = None
    _owns_store: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.storage_path = Path(self.storage_path or DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH).expanduser().resolve()
        self.backend = str(self.backend or "sqlite").strip().lower()
        if self.store is None:
            self.store = create_local_storage_engine(self.storage_path, backend=self.backend)
            self._owns_store = True
        else:
            self._owns_store = False
        self.store.ensure_schema()

    def close(self) -> None:
        if self._owns_store and self.store is not None:
            self.store.close()

    def __enter__(self) -> "ResearchAssetCoveragePlannerRuntime":
        _ = self.store.connection
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _certification_runtime(self) -> HistoricalResearchAssetCertificationRuntime:
        return _certification_runtime(self.store, self.storage_path, self.backend)

    def _lifecycle_runtime(self) -> ResearchAssetLifecycleRuntime:
        return _lifecycle_runtime(self.store, self.storage_path, self.backend)

    def _profile_and_catalog(self, profile_id: str) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        profile_id = _normalize_text(profile_id, DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID)
        certification_runtime = self._certification_runtime()
        lifecycle_runtime = self._lifecycle_runtime()
        try:
            required_catalog = [asset.as_dict() if hasattr(asset, "as_dict") else dict(asset) for asset in certification_runtime.build_required_asset_catalog(profile_id=profile_id)]
            future_catalog = [asset.as_dict() if hasattr(asset, "as_dict") else dict(asset) for asset in certification_runtime.build_discovered_future_asset_catalog(profile_id=profile_id)]
            lifecycle_identity_catalog = [asset.as_dict() if hasattr(asset, "as_dict") else dict(asset) for asset in lifecycle_runtime.build_identity_catalog(profile_id=profile_id)]
            return profile_id, required_catalog, future_catalog, lifecycle_identity_catalog
        finally:
            certification_runtime.close()
            lifecycle_runtime.close()

    def build_research_asset_coverage_registry(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID) -> list[dict[str, Any]]:
        profile_id, required_catalog, future_catalog, _ = self._profile_and_catalog(profile_id)
        asset_blueprints = list(required_catalog) + list(future_catalog)
        certification_rows = self.store.fetch("historical_research_asset_certifications", order_by="certification_id ASC") if self.store.table_exists("historical_research_asset_certifications") else []
        lifecycle_rows = self.store.fetch("research_asset_lifecycles", order_by="asset_id ASC") if self.store.table_exists("research_asset_lifecycles") else []
        provider_registry = {row["provider_id"]: row for row in self.build_provider_coverage_registry(profile_id=profile_id)}
        asset_catalog = _build_asset_catalog_for_profile(
            profile_id=profile_id,
            certification_rows=certification_rows,
            lifecycle_rows=lifecycle_rows,
            provider_registry=provider_registry,
        )
        return asset_catalog

    def build_provider_coverage_registry(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID) -> list[dict[str, Any]]:
        profile_id, required_catalog, future_catalog, _ = self._profile_and_catalog(profile_id)
        asset_blueprints = list(required_catalog) + list(future_catalog)
        provider_records = _build_provider_registry_for_profile(profile_id=profile_id, asset_catalog=asset_blueprints)
        return provider_records

    def build_coverage_gap_engine(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID) -> dict[str, Any]:
        profile_id, required_catalog, future_catalog, _ = self._profile_and_catalog(profile_id)
        certification_rows = self.store.fetch("historical_research_asset_certifications", order_by="certification_id ASC") if self.store.table_exists("historical_research_asset_certifications") else []
        lifecycle_rows = self.store.fetch("research_asset_lifecycles", order_by="asset_id ASC") if self.store.table_exists("research_asset_lifecycles") else []
        provider_registry = {row["provider_id"]: row for row in self.build_provider_coverage_registry(profile_id=profile_id)}
        asset_catalog = _build_asset_catalog_for_profile(
            profile_id=profile_id,
            certification_rows=certification_rows,
            lifecycle_rows=lifecycle_rows,
            provider_registry=provider_registry,
        )
        return _build_coverage_gap_engine(
            profile_id=profile_id,
            asset_catalog=asset_catalog,
            provider_registry=list(provider_registry.values()),
            certification_rows=certification_rows,
            lifecycle_rows=lifecycle_rows,
        )

    def build_acquisition_plan(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID) -> list[dict[str, Any]]:
        gap_engine = self.build_coverage_gap_engine(profile_id=profile_id)
        return list(gap_engine.get("next_acquisition_targets", []))

    def build_worldview_query_surface(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID) -> dict[str, Any]:
        asset_catalog = self.build_research_asset_coverage_registry(profile_id=profile_id)
        gap_engine = self.build_coverage_gap_engine(profile_id=profile_id)
        return _build_worldview_query_surface(profile_id=profile_id, asset_catalog=asset_catalog, coverage_gap_engine=gap_engine)

    def build_snapshot(
        self,
        *,
        profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
    ) -> dict[str, Any]:
        profile_id, required_catalog, future_catalog, lifecycle_identity_catalog = self._profile_and_catalog(profile_id)
        certification_runtime = self._certification_runtime()
        lifecycle_runtime = self._lifecycle_runtime()
        try:
            certification_snapshot = certification_runtime.build_readiness_snapshot(profile_id=profile_id)
            lifecycle_snapshot = lifecycle_runtime.build_readiness_snapshot(profile_id=profile_id)
        finally:
            certification_runtime.close()
            lifecycle_runtime.close()

        provider_registry = self.build_provider_coverage_registry(profile_id=profile_id)
        asset_registry = self.build_research_asset_coverage_registry(profile_id=profile_id)
        gap_engine = _build_coverage_gap_engine(
            profile_id=profile_id,
            asset_catalog=asset_registry,
            provider_registry=provider_registry,
            certification_rows=certification_snapshot.get("research_asset_certifications", []),
            lifecycle_rows=lifecycle_snapshot.get("research_asset_lifecycles", []),
        )
        worldview_query_surface = _build_worldview_query_surface(profile_id=profile_id, asset_catalog=asset_registry, coverage_gap_engine=gap_engine)
        registry_report = build_registry_report(module="americanfootball_nfl")
        registry_snapshot = build_registry()
        recommended_next = recommended_next_adapters(registry_snapshot, limit=10)
        planner_readiness = {
            "ok": True,
            "status": "ready" if gap_engine["minimum_schema_completion_percentage"] >= 100.0 and not gap_engine["connector_upgrade_asset_ids"] else "partial",
            "profile_id": profile_id,
            "required_asset_count": gap_engine["required_asset_count"],
            "certified_asset_count": gap_engine["certified_asset_count"],
            "missing_asset_count": gap_engine["missing_asset_count"],
            "connector_upgrade_asset_count": gap_engine["connector_upgrade_asset_count"],
            "minimum_schema_completion_percentage": gap_engine["minimum_schema_completion_percentage"],
            "first_production_connector_target": gap_engine["first_production_connector_target"],
        }
        return {
            "ok": True,
            "status": planner_readiness["status"],
            "schema_version": RESEARCH_ASSET_COVERAGE_PLANNER_SCHEMA_VERSION,
            "profile": {
                "profile_id": profile_id,
                "profile_family": _asset_profile_fields(profile_id)["market_family"],
            },
            "research_asset_coverage_registry": asset_registry,
            "provider_coverage_registry": provider_registry,
            "coverage_gap_engine": gap_engine,
            "acquisition_plans": list(gap_engine.get("next_acquisition_targets", [])),
            "worldview_query_surface": worldview_query_surface,
            "planner_readiness": planner_readiness,
            "certification_snapshot": certification_snapshot,
            "lifecycle_snapshot": lifecycle_snapshot,
            "identity_catalog": lifecycle_identity_catalog,
            "required_asset_catalog": required_catalog,
            "future_asset_catalog": future_catalog,
            "source_registry_report": registry_report,
            "source_registry_snapshot": registry_snapshot,
            "recommended_next_adapters": recommended_next,
            "coverage_summary": {
                "asset_count": len(asset_registry),
                "provider_count": len(provider_registry),
                "certified_assets": gap_engine["certified_required_asset_ids"],
                "missing_required_assets": gap_engine["missing_required_asset_ids"],
                "connector_upgrade_assets": gap_engine["connector_upgrade_asset_ids"],
                "future_assets": gap_engine["future_asset_ids"],
            },
            "notes": [
                "The planner is read-only. It inspects certified assets, source coverage, and readiness metadata without downloading data or enabling providers.",
                "The first production connector target remains the NFL schedule asset so the deterministic fixture can be replaced with the canonical open provider path.",
            ],
        }

    def dashboard_snapshot(self, *, profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID) -> dict[str, Any]:
        snapshot = self.build_snapshot(profile_id=profile_id)
        snapshot["coverage_planner_readiness"] = {
            "status": snapshot.get("planner_readiness", {}).get("status", "missing"),
            "minimum_schema_completion_percentage": snapshot.get("planner_readiness", {}).get("minimum_schema_completion_percentage", 0.0),
            "first_production_connector_target": snapshot.get("planner_readiness", {}).get("first_production_connector_target", ""),
            "certified_asset_count": snapshot.get("planner_readiness", {}).get("certified_asset_count", 0),
            "missing_asset_count": snapshot.get("planner_readiness", {}).get("missing_asset_count", 0),
            "connector_upgrade_asset_count": snapshot.get("planner_readiness", {}).get("connector_upgrade_asset_count", 0),
        }
        snapshot["provider_selection_summary"] = {
            "provider_count": len(snapshot.get("provider_coverage_registry", [])),
            "asset_count": len(snapshot.get("research_asset_coverage_registry", [])),
            "top_provider_ids": [row.get("provider_id") for row in snapshot.get("provider_coverage_registry", [])[:5]],
            "top_asset_ids": [row.get("research_asset_id") for row in snapshot.get("research_asset_coverage_registry", [])[:5]],
        }
        snapshot["coverage_gap_summary"] = {
            "minimum_schema_completion_percentage": snapshot.get("coverage_gap_engine", {}).get("minimum_schema_completion_percentage", 0.0),
            "first_production_connector_target": snapshot.get("coverage_gap_engine", {}).get("first_production_connector_target", ""),
            "next_acquisition_target_count": len(snapshot.get("coverage_gap_engine", {}).get("next_acquisition_targets", [])),
        }
        snapshot["dashboard_ready"] = True
        return snapshot


def build_research_asset_coverage_registry(
    *,
    profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
    storage_path: str | Path | None = None,
    backend: str = "sqlite",
) -> list[dict[str, Any]]:
    runtime = ResearchAssetCoveragePlannerRuntime(storage_path=storage_path or DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH, backend=backend)
    try:
        return runtime.build_research_asset_coverage_registry(profile_id=profile_id)
    finally:
        runtime.close()


def build_provider_coverage_registry(
    *,
    profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
    storage_path: str | Path | None = None,
    backend: str = "sqlite",
) -> list[dict[str, Any]]:
    runtime = ResearchAssetCoveragePlannerRuntime(storage_path=storage_path or DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH, backend=backend)
    try:
        return runtime.build_provider_coverage_registry(profile_id=profile_id)
    finally:
        runtime.close()


def build_coverage_gap_engine(
    *,
    profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
    storage_path: str | Path | None = None,
    backend: str = "sqlite",
) -> dict[str, Any]:
    runtime = ResearchAssetCoveragePlannerRuntime(storage_path=storage_path or DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH, backend=backend)
    try:
        return runtime.build_coverage_gap_engine(profile_id=profile_id)
    finally:
        runtime.close()


def build_acquisition_plan(
    *,
    profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
    storage_path: str | Path | None = None,
    backend: str = "sqlite",
) -> list[dict[str, Any]]:
    runtime = ResearchAssetCoveragePlannerRuntime(storage_path=storage_path or DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH, backend=backend)
    try:
        return runtime.build_acquisition_plan(profile_id=profile_id)
    finally:
        runtime.close()


def build_worldview_query_surface(
    *,
    profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
    storage_path: str | Path | None = None,
    backend: str = "sqlite",
) -> dict[str, Any]:
    runtime = ResearchAssetCoveragePlannerRuntime(storage_path=storage_path or DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH, backend=backend)
    try:
        return runtime.build_worldview_query_surface(profile_id=profile_id)
    finally:
        runtime.close()


def build_research_asset_coverage_planner_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
) -> dict[str, Any]:
    runtime = ResearchAssetCoveragePlannerRuntime(storage_path=storage_path or DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH, backend=backend)
    try:
        return runtime.build_snapshot(profile_id=profile_id)
    finally:
        runtime.close()


def build_research_asset_coverage_planner_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
) -> dict[str, Any]:
    runtime = ResearchAssetCoveragePlannerRuntime(storage_path=storage_path or DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH, backend=backend)
    try:
        return runtime.dashboard_snapshot(profile_id=profile_id)
    finally:
        runtime.close()


def get_research_asset_coverage_planner_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    profile_id: str = DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID,
) -> dict[str, Any]:
    try:
        return build_research_asset_coverage_planner_dashboard_snapshot(
            storage_path=storage_path,
            backend=backend,
            profile_id=profile_id,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "research_asset_coverage_planner_snapshot_error",
            "schema_version": RESEARCH_ASSET_COVERAGE_PLANNER_SCHEMA_VERSION,
            "profile": {
                "profile_id": profile_id,
                "profile_family": _asset_profile_fields(profile_id)["market_family"],
            },
            "research_asset_coverage_registry": [],
            "provider_coverage_registry": [],
            "coverage_gap_engine": {},
            "acquisition_plans": [],
            "worldview_query_surface": {},
            "planner_readiness": {},
            "coverage_planner_readiness": {},
            "provider_selection_summary": {},
            "coverage_gap_summary": {},
            "certification_snapshot": {},
            "lifecycle_snapshot": {},
            "identity_catalog": [],
            "required_asset_catalog": [],
            "future_asset_catalog": [],
            "source_registry_report": {},
            "source_registry_snapshot": {},
            "recommended_next_adapters": [],
            "coverage_summary": {},
            "dashboard_ready": False,
            "warnings": [str(exc)],
        }


__all__ = [
    "DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_DATASET_NAME",
    "DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_OWNER",
    "DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_PROFILE_ID",
    "DEFAULT_RESEARCH_ASSET_COVERAGE_PLANNER_STORAGE_PATH",
    "RESEARCH_ASSET_COVERAGE_PLANNER_SCHEMA_VERSION",
    "ResearchAssetCoveragePlannerRuntime",
    "build_acquisition_plan",
    "build_coverage_gap_engine",
    "build_provider_coverage_registry",
    "build_research_asset_coverage_planner_dashboard_snapshot",
    "build_research_asset_coverage_planner_snapshot",
    "build_research_asset_coverage_registry",
    "build_worldview_query_surface",
    "get_research_asset_coverage_planner_snapshot_for_dashboard",
]
