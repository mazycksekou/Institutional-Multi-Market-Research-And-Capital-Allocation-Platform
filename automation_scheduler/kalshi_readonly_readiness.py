from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .kalshi_readonly_adapter import KalshiReadonlyAdapter
from src.providers.registry import get_provider_registry

PROVIDER_ID = "kalshi_prediction_market"

REQUIRED_ENV_NAMES = (
    "KALSHI_PROVIDER_ENABLED",
    "KALSHI_LIVE_READS_ENABLED",
    "KALSHI_API_KEY",
    "KALSHI_API_SECRET",
)

OPTIONAL_ENV_NAMES = (
    "KALSHI_API_BASE_URL",
    "KALSHI_API_TIMEOUT_SECONDS",
    "KALSHI_MARKETS_PATH",
    "KALSHI_EVENTS_PATH",
)

SAFETY_FLAGS = {
    "provider_write": False,
    "execution_allowed": False,
    "execution_allowed_count": 0,
    "live_execution_enabled": False,
    "auto_execution_enabled": False,
    "kalshi_order_execution_enabled": False,
    "actual_orders_submitted": 0,
    "actual_bets_submitted": 0,
    "actual_trades_submitted": 0,
    "raw_payload_included": False,
    "secrets_included": False,
}


def resolve_project_root(start: str | Path | None = None) -> Path:
    if start:
        candidate = Path(start).resolve()
        if candidate.is_file():
            candidate = candidate.parent
    else:
        candidate = Path(__file__).resolve()
    for parent in (candidate, *candidate.parents):
        if (parent / "automation_scheduler").is_dir() and (parent / "scripts").is_dir():
            return parent
    return Path.cwd().resolve()


def load_project_env(project_root: str | Path | None = None) -> dict[str, Any]:
    root = resolve_project_root(project_root)
    env_path = root / ".env"
    result = {
        "env_file_present": env_path.exists(),
        "env_loaded": False,
        "env_loader": "not_available",
    }
    if not env_path.exists():
        return result
    try:
        from dotenv import load_dotenv
    except Exception:
        result["env_loader"] = "python_dotenv_unavailable"
        return result
    load_dotenv(dotenv_path=env_path, override=False)
    result["env_loaded"] = True
    result["env_loader"] = "python_dotenv"
    return result


def build_kalshi_readonly_contract() -> dict[str, Any]:
    return dict(get_provider_registry(include_legacy_aliases=True).get(PROVIDER_ID, {}))


def build_kalshi_readonly_adapter() -> KalshiReadonlyAdapter:
    return KalshiReadonlyAdapter(build_kalshi_readonly_contract())


def _env_present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_blocker(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "blocked_missing_credentials": "credentials_missing",
        "missing_credentials": "credentials_missing",
        "provider_disabled": "provider_not_ready",
        "live_reads_disabled": "live_reads_disabled",
        "dry_run_required": "provider_not_ready",
        "auto_execution_not_allowed": "provider_not_ready",
        "read_only_required": "provider_not_ready",
    }
    cleaned = mapping.get(text, text or "unknown")
    if any(token in cleaned for token in ("secret", "token", "password", "api_key_value", "credential_value")):
        return "provider_not_ready"
    return cleaned


def _missing_env_names() -> list[str]:
    return [name for name in REQUIRED_ENV_NAMES if not _env_present(name)]


def _disabled_env_names() -> list[str]:
    disabled: list[str] = []
    for name in ("KALSHI_PROVIDER_ENABLED", "KALSHI_LIVE_READS_ENABLED"):
        if _env_present(name) and not _env_truthy(name):
            disabled.append(name)
    return disabled


def _recommended_next_action(*, cfg: dict[str, Any], missing_env_names: list[str], disabled_env_names: list[str]) -> str:
    blockers = {_safe_blocker(item) for item in list(cfg.get("blockers") or [])}
    if bool(cfg.get("ok")):
        return "ready_for_deepseek_tiny_provider_check"
    if missing_env_names:
        return "set_missing_kalshi_readonly_env_names"
    if disabled_env_names:
        return "turn_on_read_only_kalshi_env_flags"
    if "credentials_missing" in blockers:
        return "set_missing_kalshi_readonly_env_names"
    if "live_reads_disabled" in blockers:
        return "enable_read_only_live_reads"
    if "provider_not_ready" in blockers:
        return "enable_read_only_provider_config"
    return "review_safe_readiness_blockers"


def build_kalshi_readonly_readiness_report(
    *,
    project_root: str | Path | None = None,
    load_env: bool = True,
    tiny_connectivity_check: bool = False,
    adapter: KalshiReadonlyAdapter | None = None,
) -> dict[str, Any]:
    root = resolve_project_root(project_root)
    env_load = load_project_env(root) if load_env else {
        "env_file_present": (root / ".env").exists(),
        "env_loaded": False,
        "env_loader": "not_requested",
    }
    adapter = adapter or build_kalshi_readonly_adapter()
    cfg = adapter.validate_config()
    blockers = sorted({_safe_blocker(item) for item in list(cfg.get("blockers") or [])})
    missing = _missing_env_names()
    disabled = _disabled_env_names()
    report: dict[str, Any] = {
        "status": "ok",
        "provider_id": PROVIDER_ID,
        "project_root_resolved": True,
        "env_file_present": bool(env_load.get("env_file_present")),
        "env_loaded": bool(env_load.get("env_loaded")),
        "env_loader": env_load.get("env_loader"),
        "provider_readiness_status": "provider_ready" if bool(cfg.get("ok")) else "provider_not_ready",
        "provider_readiness_blockers": blockers,
        "provider_config_present": bool(cfg.get("provider_enabled")),
        "credentials_present": str(cfg.get("credential_status") or "") == "ok",
        "live_reads_enabled": bool(cfg.get("live_reads_enabled")),
        "missing_env_names": missing,
        "disabled_env_names": disabled,
        "required_env_names": list(REQUIRED_ENV_NAMES),
        "optional_env_names": list(OPTIONAL_ENV_NAMES),
        "tiny_connectivity_check_requested": bool(tiny_connectivity_check),
        "tiny_connectivity_check_status": "not_requested",
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "rate_limited": False,
        "recommended_next_action": _recommended_next_action(cfg=cfg, missing_env_names=missing, disabled_env_names=disabled),
        **SAFETY_FLAGS,
    }
    if not tiny_connectivity_check:
        return report
    if not bool(cfg.get("ok")):
        report["tiny_connectivity_check_status"] = "skipped_provider_not_ready"
        return report

    report["provider_calls_attempted"] = 1
    fetch = adapter.fetch_markets(params={"limit": 1})
    status = _safe_blocker(fetch.get("status") or fetch.get("blocker") or "unknown")
    report["tiny_connectivity_check_status"] = status
    report["provider_calls_succeeded"] = 1 if bool(fetch.get("ok")) and status == "ok" else 0
    report["provider_calls_failed"] = 0 if report["provider_calls_succeeded"] else 1
    report["rate_limited"] = int(fetch.get("http_status") or 0) == 429 or _safe_blocker(fetch.get("blocker")) == "http_429"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local Kalshi read-only readiness without printing secrets.")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--tiny-connectivity-check", action="store_true")
    parser.add_argument("--no-env-load", action="store_true")
    args = parser.parse_args(argv)
    report = build_kalshi_readonly_readiness_report(
        project_root=args.project_root,
        load_env=not args.no_env_load,
        tiny_connectivity_check=args.tiny_connectivity_check,
    )
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
