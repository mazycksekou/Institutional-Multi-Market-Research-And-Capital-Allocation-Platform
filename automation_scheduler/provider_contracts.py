from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.providers.contracts import (
    PROVIDER_CONTRACT_SCHEMA_VERSION,
    PROVIDER_SCHEMA_VERSION,
    PROVIDER_TYPES,
    ProviderContract,
    build_provider_contract,
    build_scaffold_provider_contract,
    ensure_provider_runtime_directories,
    get_default_provider_contracts as _canonical_get_default_provider_contracts,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_default_provider_contracts() -> dict[str, dict[str, Any]]:
    contracts = dict(_canonical_get_default_provider_contracts())
    if "prediction_market_placeholder" in contracts:
        contracts["kalshi_placeholder"] = dict(contracts["prediction_market_placeholder"])
    return contracts


def write_provider_contract_snapshot(base_data_dir: str = "data") -> str:
    paths = ensure_provider_runtime_directories(base_data_dir)
    payload = {
        "schema_version": PROVIDER_CONTRACT_SCHEMA_VERSION,
        "written_at": _utc_now_iso(),
        "providers": get_default_provider_contracts(),
        "dry_run": True,
    }
    path = Path(paths["provider_contracts"]) / "provider_contracts.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)


__all__ = [
    "PROVIDER_CONTRACT_SCHEMA_VERSION",
    "PROVIDER_SCHEMA_VERSION",
    "PROVIDER_TYPES",
    "ProviderContract",
    "build_provider_contract",
    "build_scaffold_provider_contract",
    "ensure_provider_runtime_directories",
    "get_default_provider_contracts",
    "write_provider_contract_snapshot",
]
