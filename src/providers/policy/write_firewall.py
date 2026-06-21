from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .allowlist import _locked_safety_flags, classify_provider
from .secret_policy import redact_mapping


WRITE_ALLOWLIST: dict[str, set[str]] = {}


@dataclass(slots=True)
class ProviderWritePolicy:
    provider_name: str = ""
    action_name: str = ""
    policy_status: str = "scaffold_only"
    write_allowlist: dict[str, list[str]] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=lambda: ["scaffold_only"])

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "action_name": self.action_name,
            "policy_status": self.policy_status,
            "write_allowlist": {key: list(value) for key, value in self.write_allowlist.items()},
            "blockers": list(self.blockers),
            "ok": False,
        }


ProviderWriteFirewallPolicy = ProviderWritePolicy


def build_scaffold_provider_write_policy(provider_name: str = "", action_name: str = "") -> ProviderWritePolicy:
    return ProviderWritePolicy(provider_name=provider_name, action_name=action_name)


def build_scaffold_write_firewall_policy(provider_name: str = "", action_name: str = "") -> ProviderWritePolicy:
    return build_scaffold_provider_write_policy(provider_name=provider_name, action_name=action_name)


def _base_data_dir(base_data_dir: str | None = None) -> Path:
    return Path(base_data_dir).expanduser().resolve() if base_data_dir else Path.cwd().resolve()


def _audit_dir(base_data_dir: str | None = None) -> Path:
    path = _base_data_dir(base_data_dir) / "security" / "audit"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _load_existing_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [item for item in payload["items"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _timestamp_seed(provider_name: str, action_name: str, request_payload: dict[str, Any], response_payload: dict[str, Any]) -> str:
    request_seed = hashlib.sha256(json.dumps(request_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    response_seed = hashlib.sha256(json.dumps(response_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return "|".join([provider_name, action_name, request_seed[:16], response_seed[:16]])


def check_provider_write_attempt(
    *,
    provider: str | None,
    action: str | None,
    request_payload: dict[str, Any] | None = None,
    owner_approval: dict[str, Any] | None = None,
    risk_limits: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    execution_mode: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
) -> dict[str, Any]:
    request_payload = request_payload if isinstance(request_payload, dict) else {}
    provider_name = str(provider or request_payload.get("provider") or "unknown")
    action_name = str(action or request_payload.get("action") or "unknown")
    provider_class = classify_provider(provider_name)
    allowed_actions = WRITE_ALLOWLIST.get(provider_name, set())
    safe_request = redact_mapping(request_payload)
    safe_response = {
        "provider": provider_name,
        "action": action_name,
        "provider_class": provider_class,
        "request_payload": safe_request,
        "owner_approval_present": bool(owner_approval),
        "risk_limits_present": bool(risk_limits),
        "idempotency_key_present": bool(idempotency_key),
        "execution_mode": execution_mode,
        "base_data_dir": bool(base_data_dir),
    }

    blockers = {
        "provider_not_write_allowlisted",
        "action_not_write_allowlisted",
        "execution_mode_not_enabled",
        "owner_approval_invalid",
        "risk_limit_blocked",
        "kill_switch_active",
        "idempotency_key_missing",
        "global_execution_locked",
        "provider_write_default_false",
    }
    if provider_name in WRITE_ALLOWLIST and action_name in allowed_actions:
        blockers.discard("provider_not_write_allowlisted")
        blockers.discard("action_not_write_allowlisted")
    if execution_mode in {"sandbox_owner_approved", "live_owner_approved"}:
        blockers.discard("execution_mode_not_enabled")
    if owner_approval:
        blockers.discard("owner_approval_invalid")
    if risk_limits:
        blockers.discard("risk_limit_blocked")
    if idempotency_key:
        blockers.discard("idempotency_key_missing")

    result = {
        "ok": False,
        "status": "provider_write_blocked",
        "provider_name": provider_name,
        "provider_class": provider_class,
        "action_requested": action_name,
        "write_blockers": sorted(blockers),
        "owner_approval_status": "scaffold_only" if owner_approval else "missing",
        "risk_limit_status": "scaffold_only" if risk_limits else "execution_locked",
        "kill_switches_active": True,
        "idempotency_key_present": bool(idempotency_key),
        "replay_protection_required": True,
        "audit_ledger_required": True,
        **_locked_safety_flags(),
    }

    if persist_audit:
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_path = _audit_dir(base_data_dir) / f"{timestamp[:10]}.json"
        items = _load_existing_items(audit_path)
        record = {
            "event_id": f"security_event_{hashlib.sha256(_timestamp_seed(provider_name, action_name, safe_request, safe_response).encode('utf-8')).hexdigest()[:24]}",
            "event_type": "provider_write_blocked",
            "timestamp": timestamp,
            "actor_type": str(request_payload.get("actor_type") or "system"),
            "actor_provider": str(request_payload.get("actor_provider") or ""),
            "action_requested": action_name,
            "action_allowed": False,
            "denial_reason": ";".join(result["write_blockers"]),
            "asset_type": request_payload.get("asset_type"),
            "market_type": request_payload.get("market_type"),
            "provider_name": provider_name,
            "request_hash": hashlib.sha256(json.dumps(safe_request, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
            "response_hash": hashlib.sha256(json.dumps(safe_response, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
            "redacted": True,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "raw_payload_exposed": False,
            "raw_payload_included": False,
            "secrets_detected": False,
            "secrets_included": False,
            "request_payload": safe_request,
            "response_payload": safe_response,
            **_locked_safety_flags(),
        }
        items.append(record)
        wrapper = {
            "ok": True,
            "status": "ok",
            "storage_backend": "file",
            "date": timestamp[:10],
            "last_updated_at": timestamp,
            "count": len(items),
            "items": items,
            **_locked_safety_flags(),
        }
        _atomic_write_json(audit_path, wrapper)

    return result
