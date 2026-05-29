from __future__ import annotations

from typing import Any

from .provider_health import compact_provider_health
from .provider_payload_validator import validate_provider_payload
from .scheduler_config import utc_now_iso


class ProviderAdapterBase:
    def __init__(self, contract: dict[str, Any]):
        self.contract = dict(contract)
        self.contract.setdefault("enabled", False)
        self.contract.setdefault("dry_run", True)
        self.contract.setdefault("live_calls_enabled", False)

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": self.contract.get("provider_id"),
            "provider_name": self.contract.get("provider_name"),
            "provider_type": self.contract.get("provider_type"),
            "supports_streaming": bool(self.contract.get("supports_streaming", False)),
            "supports_polling": bool(self.contract.get("supports_polling", True)),
            "supported_markets": list(self.contract.get("supported_markets", [])),
            "output_schema_version": self.contract.get("output_schema_version"),
            "enabled": bool(self.contract.get("enabled", False)),
            "dry_run": bool(self.contract.get("dry_run", True)),
            "live_calls_enabled": bool(self.contract.get("live_calls_enabled", False)),
        }

    def validate_config(self) -> dict[str, Any]:
        blockers = []
        if not self.contract.get("enabled", False):
            blockers.append("disabled_provider")
        if not self.contract.get("live_calls_enabled", False):
            blockers.append("live_calls_disabled")
        if self.contract.get("required_credentials") and self.contract.get("credential_status") != "ok":
            blockers.append("missing_credentials")
        if self.contract.get("dry_run", True):
            blockers.append("dry_run_placeholder")
        return {
            "ok": len(blockers) == 0,
            "blockers": blockers,
            "status": "ready" if len(blockers) == 0 else "blocked",
        }

    def health_check(self) -> dict[str, Any]:
        result = self.validate_config()
        return compact_provider_health(self.contract, blockers=result["blockers"])

    def fetch_snapshot(self) -> dict[str, Any]:
        return {
            "provider_id": self.contract.get("provider_id"),
            "provider_type": self.contract.get("provider_type"),
            "timestamp": utc_now_iso(),
            "status": "dry_run_placeholder",
            "records": [],
            "dry_run": True,
        }

    def normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return dict(payload)

    def validate_payload(self, payload: dict[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
        return validate_provider_payload(
            str(self.contract.get("provider_type") or ""),
            payload,
            max_staleness_seconds=max_staleness_seconds,
        )

