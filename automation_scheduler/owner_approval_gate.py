from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit_ledger import append_security_event
from .data_paths import resolve_base_data_dir
from .scheduler_config import hash_payload, sanitize_filename
from .security_event_types import OWNER_APPROVAL_EXPIRED, OWNER_APPROVAL_INVALID, OWNER_APPROVAL_MISSING, NONCE_REPLAY_DETECTED
from .security_policy import locked_safety_flags


SCOPE_FIELDS = ("action", "asset_type", "market_type", "provider", "max_size", "max_notional", "time_window", "approval_expires_at")


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _canonical_scope(scope: dict[str, Any]) -> dict[str, Any]:
    return {field: scope.get(field) for field in SCOPE_FIELDS if scope.get(field) is not None}


def _scope_matches(approval_scope: dict[str, Any], requested_scope: dict[str, Any]) -> bool:
    approved = _canonical_scope(approval_scope)
    requested = _canonical_scope(requested_scope)
    for key, value in requested.items():
        if approved.get(key) != value:
            return False
    return True


def sign_owner_approval(
    *,
    approval_scope: dict[str, Any],
    approval_nonce: str,
    owner_email_hash: str,
    owner_user_id: str,
    owner_approval_timestamp: str,
    approval_expires_at: str,
    signing_secret: str,
) -> str:
    message = json.dumps(
        {
            "approval_scope": _canonical_scope({**approval_scope, "approval_expires_at": approval_expires_at}),
            "approval_nonce": approval_nonce,
            "owner_email_hash": owner_email_hash,
            "owner_user_id": owner_user_id,
            "owner_approval_timestamp": owner_approval_timestamp,
            "approval_expires_at": approval_expires_at,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hmac.new(signing_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _approval_signature_valid(approval: dict[str, Any], signing_secret: str | None) -> bool:
    if not signing_secret:
        return False
    supplied = str(approval.get("approval_signature") or "")
    if not supplied:
        return False
    expected = sign_owner_approval(
        approval_scope=dict(approval.get("approval_scope") or {}),
        approval_nonce=str(approval.get("approval_nonce") or ""),
        owner_email_hash=str(approval.get("owner_email_hash") or ""),
        owner_user_id=str(approval.get("owner_user_id") or ""),
        owner_approval_timestamp=str(approval.get("owner_approval_timestamp") or ""),
        approval_expires_at=str(approval.get("approval_expires_at") or ""),
        signing_secret=signing_secret,
    )
    return hmac.compare_digest(supplied, expected)


def _nonce_store_path(base_data_dir: str | None = None) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "security" / "owner_approvals" / "used_nonces.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_used_nonces(base_data_dir: str | None = None) -> set[str]:
    path = _nonce_store_path(base_data_dir)
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if isinstance(payload, list):
        return {str(item) for item in payload}
    if isinstance(payload, dict) and isinstance(payload.get("nonces"), list):
        return {str(item) for item in payload["nonces"]}
    return set()


def _write_used_nonces(nonces: set[str], base_data_dir: str | None = None) -> None:
    path = _nonce_store_path(base_data_dir)
    ordered = sorted(nonces)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps({"nonces": ordered}, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def evaluate_owner_approval(
    approval: dict[str, Any] | None,
    *,
    requested_scope: dict[str, Any] | None = None,
    actor_type: str = "system",
    signing_secret: str | None = None,
    used_nonces: set[str] | None = None,
    persist_nonce: bool = False,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    requested_scope = requested_scope or {}
    approval = approval if isinstance(approval, dict) else {}
    present = bool(approval.get("owner_approval_present"))
    scope = dict(approval.get("approval_scope") or {})
    nonce = str(approval.get("approval_nonce") or "")
    expires_at = approval.get("approval_expires_at")
    expires_at_dt = _parse_timestamp(expires_at)
    audit_record_present = bool(approval.get("audit_event_id") or approval.get("audit_record_present") is True)
    signature_valid = _approval_signature_valid(approval, signing_secret)
    replay_source = set(used_nonces or set())
    if persist_nonce:
        replay_source.update(_read_used_nonces(base_data_dir))
    replay_detected = bool(nonce and nonce in replay_source)

    denial_reason = None
    event_type = OWNER_APPROVAL_INVALID
    if not present:
        denial_reason = "owner_approval_missing"
        event_type = OWNER_APPROVAL_MISSING
    elif actor_type == "ai_provider":
        denial_reason = "ai_cannot_create_owner_approval"
    elif not audit_record_present:
        denial_reason = "approval_without_audit_record"
    elif not nonce:
        denial_reason = "approval_nonce_missing"
    elif replay_detected:
        denial_reason = "approval_nonce_replay"
        event_type = NONCE_REPLAY_DETECTED
    elif expires_at_dt is None:
        denial_reason = "approval_expiration_missing_or_invalid"
    elif expires_at_dt <= now:
        denial_reason = "owner_approval_expired"
        event_type = OWNER_APPROVAL_EXPIRED
    elif not signature_valid:
        denial_reason = "owner_approval_signature_invalid"
    elif requested_scope and not _scope_matches(scope, requested_scope):
        denial_reason = "approval_scope_mismatch"

    valid = denial_reason is None
    if valid and persist_nonce and nonce:
        replay_source.add(nonce)
        _write_used_nonces(replay_source, base_data_dir)
    status = "owner_approval_valid" if valid else "owner_approval_blocked"
    result = {
        "ok": valid,
        "status": status,
        "owner_user_id": approval.get("owner_user_id"),
        "owner_email_hash": approval.get("owner_email_hash"),
        "owner_approval_required": True,
        "owner_approval_present": present,
        "owner_approval_timestamp": approval.get("owner_approval_timestamp"),
        "approval_scope": _canonical_scope(scope),
        "approval_expires_at": expires_at,
        "approval_nonce": nonce or None,
        "approval_signature_valid": bool(signature_valid),
        "approval_replay_detected": replay_detected,
        "approval_status": "valid" if valid else "denied",
        "approval_denial_reason": denial_reason,
        "approval_audit_record_present": audit_record_present,
        "approval_scope_hash": hash_payload(_canonical_scope(scope)) if scope else None,
        **locked_safety_flags(),
    }
    result["execution_allowed"] = False
    if persist_audit and not valid:
        append_security_event(
            event_type=event_type,
            actor_type=actor_type,
            actor_provider=approval.get("actor_provider"),
            action_requested="owner_approval_validate",
            denial_reason=denial_reason,
            provider_name=requested_scope.get("provider"),
            asset_type=requested_scope.get("asset_type"),
            market_type=requested_scope.get("market_type"),
            request_payload={"approval": approval, "requested_scope": requested_scope},
            response_payload=result,
            base_data_dir=base_data_dir,
        )
    return result


def compact_owner_approval_for_audit(approval: dict[str, Any]) -> dict[str, Any]:
    return {
        "owner_user_id": approval.get("owner_user_id"),
        "owner_email_hash": approval.get("owner_email_hash"),
        "approval_scope_hash": hash_payload(approval.get("approval_scope") or {}),
        "approval_nonce_hash": hash_payload(approval.get("approval_nonce") or ""),
        "approval_expires_at": approval.get("approval_expires_at"),
        "approval_status": approval.get("approval_status"),
        "redacted": True,
    }
