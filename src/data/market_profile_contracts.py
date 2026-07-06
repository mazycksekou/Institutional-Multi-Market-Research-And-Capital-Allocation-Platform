from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping


def _normalize_text(value: Any, default: str = "") -> str:
    return str(value if value is not None else default).strip()


def _normalize_items(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        values = (values,)
    normalized = tuple(item for item in (_normalize_text(value) for value in values) if item)
    return normalized


@dataclass(slots=True, frozen=True)
class MarketProfileContract:
    profile_id: str
    profile_family: str
    canonical_identifiers: tuple[str, ...] = ()
    required_timestamps: tuple[str, ...] = ()
    canonical_fields: tuple[str, ...] = ()
    atomic_feature_groups: tuple[str, ...] = ()
    composite_feature_groups: tuple[str, ...] = ()
    validation_rules: tuple[str, ...] = ()
    leakage_rules: tuple[str, ...] = ()
    storage_requirements: tuple[str, ...] = ()
    feature_store_requirements: tuple[str, ...] = ()
    backtest_requirements: tuple[str, ...] = ()
    streamlit_requirements: tuple[str, ...] = ()
    research_requirements: tuple[str, ...] = ()
    worldview_permissions: tuple[str, ...] = ()
    paper_trading_requirements: tuple[str, ...] = ()
    live_execution_gates: tuple[str, ...] = ()
    description: str = ""
    market_scope: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _normalize_text(self.profile_id))
        object.__setattr__(self, "profile_family", _normalize_text(self.profile_family))
        object.__setattr__(self, "canonical_identifiers", _normalize_items(self.canonical_identifiers))
        object.__setattr__(self, "required_timestamps", _normalize_items(self.required_timestamps))
        object.__setattr__(self, "canonical_fields", _normalize_items(self.canonical_fields))
        object.__setattr__(self, "atomic_feature_groups", _normalize_items(self.atomic_feature_groups))
        object.__setattr__(self, "composite_feature_groups", _normalize_items(self.composite_feature_groups))
        object.__setattr__(self, "validation_rules", _normalize_items(self.validation_rules))
        object.__setattr__(self, "leakage_rules", _normalize_items(self.leakage_rules))
        object.__setattr__(self, "storage_requirements", _normalize_items(self.storage_requirements))
        object.__setattr__(self, "feature_store_requirements", _normalize_items(self.feature_store_requirements))
        object.__setattr__(self, "backtest_requirements", _normalize_items(self.backtest_requirements))
        object.__setattr__(self, "streamlit_requirements", _normalize_items(self.streamlit_requirements))
        object.__setattr__(self, "research_requirements", _normalize_items(self.research_requirements))
        object.__setattr__(self, "worldview_permissions", _normalize_items(self.worldview_permissions))
        object.__setattr__(self, "paper_trading_requirements", _normalize_items(self.paper_trading_requirements))
        object.__setattr__(self, "live_execution_gates", _normalize_items(self.live_execution_gates))
        object.__setattr__(self, "description", _normalize_text(self.description))
        object.__setattr__(self, "market_scope", _normalize_text(self.market_scope))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def create(
        cls,
        profile_id: str,
        profile_family: str,
        *,
        canonical_identifiers: Any = (),
        required_timestamps: Any = (),
        canonical_fields: Any = (),
        atomic_feature_groups: Any = (),
        composite_feature_groups: Any = (),
        validation_rules: Any = (),
        leakage_rules: Any = (),
        storage_requirements: Any = (),
        feature_store_requirements: Any = (),
        backtest_requirements: Any = (),
        streamlit_requirements: Any = (),
        research_requirements: Any = (),
        worldview_permissions: Any = (),
        paper_trading_requirements: Any = (),
        live_execution_gates: Any = (),
        description: str = "",
        market_scope: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> "MarketProfileContract":
        return cls(
            profile_id=profile_id,
            profile_family=profile_family,
            canonical_identifiers=_normalize_items(canonical_identifiers),
            required_timestamps=_normalize_items(required_timestamps),
            canonical_fields=_normalize_items(canonical_fields),
            atomic_feature_groups=_normalize_items(atomic_feature_groups),
            composite_feature_groups=_normalize_items(composite_feature_groups),
            validation_rules=_normalize_items(validation_rules),
            leakage_rules=_normalize_items(leakage_rules),
            storage_requirements=_normalize_items(storage_requirements),
            feature_store_requirements=_normalize_items(feature_store_requirements),
            backtest_requirements=_normalize_items(backtest_requirements),
            streamlit_requirements=_normalize_items(streamlit_requirements),
            research_requirements=_normalize_items(research_requirements),
            worldview_permissions=_normalize_items(worldview_permissions),
            paper_trading_requirements=_normalize_items(paper_trading_requirements),
            live_execution_gates=_normalize_items(live_execution_gates),
            description=description,
            market_scope=market_scope,
            metadata=metadata or {},
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "MarketProfileContract":
        return cls.create(
            profile_id=str(data.get("profile_id") or data.get("id") or ""),
            profile_family=str(data.get("profile_family") or data.get("family") or ""),
            canonical_identifiers=data.get("canonical_identifiers") or (),
            required_timestamps=data.get("required_timestamps") or (),
            canonical_fields=data.get("canonical_fields") or (),
            atomic_feature_groups=data.get("atomic_feature_groups") or (),
            composite_feature_groups=data.get("composite_feature_groups") or (),
            validation_rules=data.get("validation_rules") or (),
            leakage_rules=data.get("leakage_rules") or (),
            storage_requirements=data.get("storage_requirements") or (),
            feature_store_requirements=data.get("feature_store_requirements") or (),
            backtest_requirements=data.get("backtest_requirements") or (),
            streamlit_requirements=data.get("streamlit_requirements") or (),
            research_requirements=data.get("research_requirements") or (),
            worldview_permissions=data.get("worldview_permissions") or (),
            paper_trading_requirements=data.get("paper_trading_requirements") or (),
            live_execution_gates=data.get("live_execution_gates") or (),
            description=str(data.get("description") or ""),
            market_scope=str(data.get("market_scope") or data.get("market") or ""),
            metadata=dict(data.get("metadata") or {}),
        )

    def with_metadata(self, **metadata: Any) -> "MarketProfileContract":
        updated = dict(self.metadata)
        updated.update(metadata)
        return replace(self, metadata=updated)

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_family": self.profile_family,
            "canonical_identifiers": list(self.canonical_identifiers),
            "required_timestamps": list(self.required_timestamps),
            "canonical_fields": list(self.canonical_fields),
            "atomic_feature_groups": list(self.atomic_feature_groups),
            "composite_feature_groups": list(self.composite_feature_groups),
            "validation_rules": list(self.validation_rules),
            "leakage_rules": list(self.leakage_rules),
            "storage_requirements": list(self.storage_requirements),
            "feature_store_requirements": list(self.feature_store_requirements),
            "backtest_requirements": list(self.backtest_requirements),
            "streamlit_requirements": list(self.streamlit_requirements),
            "research_requirements": list(self.research_requirements),
            "worldview_permissions": list(self.worldview_permissions),
            "paper_trading_requirements": list(self.paper_trading_requirements),
            "live_execution_gates": list(self.live_execution_gates),
            "description": self.description,
            "market_scope": self.market_scope,
            "metadata": dict(self.metadata),
        }


def build_market_profile_contract(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> MarketProfileContract:
    data = dict(payload or {})
    data.update(overrides)
    return MarketProfileContract.from_mapping(data)


def validate_market_profile_contract(contract: MarketProfileContract | Mapping[str, Any]) -> dict[str, Any]:
    profile = contract if isinstance(contract, MarketProfileContract) else MarketProfileContract.from_mapping(contract)
    errors: list[str] = []
    warnings: list[str] = []

    if not profile.profile_id:
        errors.append("profile_id is required")
    if not profile.profile_family:
        errors.append("profile_family is required")

    required_tuple_fields = {
        "canonical_identifiers": profile.canonical_identifiers,
        "required_timestamps": profile.required_timestamps,
        "canonical_fields": profile.canonical_fields,
        "validation_rules": profile.validation_rules,
        "leakage_rules": profile.leakage_rules,
        "storage_requirements": profile.storage_requirements,
        "feature_store_requirements": profile.feature_store_requirements,
        "backtest_requirements": profile.backtest_requirements,
        "streamlit_requirements": profile.streamlit_requirements,
        "research_requirements": profile.research_requirements,
        "worldview_permissions": profile.worldview_permissions,
        "paper_trading_requirements": profile.paper_trading_requirements,
        "live_execution_gates": profile.live_execution_gates,
    }
    for field_name, values in required_tuple_fields.items():
        if not values:
            errors.append(f"{field_name} is required")

    if len(profile.canonical_identifiers) != len(set(profile.canonical_identifiers)):
        errors.append("canonical_identifiers must be unique")
    if len(profile.required_timestamps) != len(set(profile.required_timestamps)):
        errors.append("required_timestamps must be unique")
    if len(profile.canonical_fields) != len(set(profile.canonical_fields)):
        errors.append("canonical_fields must be unique")

    normalized_fields = {item.lower() for item in profile.canonical_fields}
    if profile.profile_family == "sports" and "league" not in normalized_fields:
        warnings.append("sports profile should include league in canonical_fields")
    if profile.profile_family == "prediction_markets" and "contract_id" not in normalized_fields:
        warnings.append("prediction market profile should include contract_id in canonical_fields")
    if profile.profile_family == "options_0dte" and "expiration" not in normalized_fields:
        warnings.append("options profile should include expiration in canonical_fields")

    return {
        "ok": not errors,
        "profile_id": profile.profile_id,
        "profile_family": profile.profile_family,
        "errors": errors,
        "warnings": warnings,
        "profile": profile,
    }
