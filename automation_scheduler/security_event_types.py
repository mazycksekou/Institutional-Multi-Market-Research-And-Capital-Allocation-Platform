from __future__ import annotations


AI_PROVIDER_SELECTED = "ai_provider_selected"
AI_PROVIDER_REJECTED = "ai_provider_rejected"
RED_TEAM_REVIEW_CREATED = "red_team_review_created"
EXECUTION_ATTEMPT_BLOCKED = "execution_attempt_blocked"
PROVIDER_WRITE_BLOCKED = "provider_write_blocked"
OWNER_APPROVAL_MISSING = "owner_approval_missing"
OWNER_APPROVAL_INVALID = "owner_approval_invalid"
OWNER_APPROVAL_EXPIRED = "owner_approval_expired"
NONCE_REPLAY_DETECTED = "nonce_replay_detected"
KILL_SWITCH_TRIGGERED = "kill_switch_triggered"
RISK_LIMIT_BLOCKED = "risk_limit_blocked"
SECRET_REDACTION_APPLIED = "secret_redaction_applied"
FORBIDDEN_PROVIDER_REJECTED = "forbidden_provider_rejected"
EXECUTION_FLAG_CHANGE_ATTEMPT_BLOCKED = "execution_flag_change_attempt_blocked"
AI_EXECUTION_AUTHORITY_BLOCKED = "ai_execution_authority_blocked"


SECURITY_EVENT_TYPES = {
    AI_PROVIDER_SELECTED,
    AI_PROVIDER_REJECTED,
    RED_TEAM_REVIEW_CREATED,
    EXECUTION_ATTEMPT_BLOCKED,
    PROVIDER_WRITE_BLOCKED,
    OWNER_APPROVAL_MISSING,
    OWNER_APPROVAL_INVALID,
    OWNER_APPROVAL_EXPIRED,
    NONCE_REPLAY_DETECTED,
    KILL_SWITCH_TRIGGERED,
    RISK_LIMIT_BLOCKED,
    SECRET_REDACTION_APPLIED,
    FORBIDDEN_PROVIDER_REJECTED,
    EXECUTION_FLAG_CHANGE_ATTEMPT_BLOCKED,
    AI_EXECUTION_AUTHORITY_BLOCKED,
}


def normalize_event_type(event_type: str | None) -> str:
    value = str(event_type or "").strip().lower()
    return value if value in SECURITY_EVENT_TYPES else EXECUTION_ATTEMPT_BLOCKED
