from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any


RESEARCH_DATA_ROOT_ENV = "RESEARCH_DATA_ROOT"
AUTOMATION_DATA_DIR_ENV = "AUTOMATION_DATA_DIR"
# Preserve existing deployments when both env vars are present.
_STORAGE_ENV_PRIORITY = (AUTOMATION_DATA_DIR_ENV, RESEARCH_DATA_ROOT_ENV)
_STORAGE_PROBE_NAME = ".research_data_root_probe"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_local_root() -> Path:
    return _repo_root() / "data"


def _is_render_runtime() -> bool:
    return any(
        os.getenv(name)
        for name in (
            "RENDER",
            "RENDER_SERVICE_ID",
            "RENDER_EXTERNAL_HOSTNAME",
            "RENDER_INSTANCE_ID",
        )
    )


def _configured_root() -> tuple[Path | None, str | None]:
    for env_var in _STORAGE_ENV_PRIORITY:
        raw = os.getenv(env_var)
        if raw is None or not raw.strip():
            continue
        return Path(raw.strip()).expanduser().resolve(), env_var
    return None, None


def _selected_root() -> tuple[Path, bool, str | None]:
    configured_root, configured_via_env_var = _configured_root()
    if configured_root is not None:
        return configured_root, True, configured_via_env_var
    return _repo_local_root().resolve(), False, None


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _nearest_existing_anchor(path: Path) -> Path | None:
    candidate = path.resolve()
    while True:
        try:
            if candidate.exists():
                return candidate
        except OSError:
            return None
        parent = candidate.parent
        if parent == candidate:
            return None
        candidate = parent


def _probe_root_access(root: Path) -> tuple[bool, bool, str | None]:
    probe = root / _STORAGE_PROBE_NAME
    read_ok = False
    write_ok = False
    error = None
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
        write_ok = True
        read_ok = probe.read_text(encoding="utf-8") == "ok"
    except Exception as exc:
        error = exc.__class__.__name__
    finally:
        try:
            probe.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            pass
    return read_ok, write_ok, error


def _free_space(root: Path) -> tuple[int | None, Path | None]:
    anchor = root if root.exists() else _nearest_existing_anchor(root)
    if anchor is None:
        return None, None
    try:
        return int(shutil.disk_usage(anchor).free), anchor
    except Exception:
        return None, anchor


def _render_mount_valid(root_text: str, configured: bool) -> bool:
    if os.name == "nt" or not _is_render_runtime() or not configured:
        return True
    return root_text == "/var/data" or root_text.startswith("/var/data/")


def get_automation_data_dir() -> Path:
    root, _, _ = _selected_root()
    return root


def resolve_base_data_dir(base_data_dir: str | Path | None = None) -> Path:
    if base_data_dir is None:
        return get_automation_data_dir()
    path = Path(base_data_dir).expanduser()
    if str(path).replace("\\", "/").rstrip("/") == "data":
        return get_automation_data_dir()
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ensure_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"runtime data path escapes {AUTOMATION_DATA_DIR_ENV}") from exc
    return resolved


def get_runtime_data_path(*parts: str | os.PathLike[str]) -> Path:
    root = get_automation_data_dir()
    path = root
    for part in parts:
        part_path = Path(part)
        if part_path.is_absolute():
            raise ValueError(f"runtime data path part must be relative: {part}")
        path = path / part_path
    return _ensure_under_root(path, root)


def get_review_queue_dir() -> Path:
    return get_runtime_data_path("review_queue")


def get_paper_ledger_dir() -> Path:
    return get_runtime_data_path("paper_ledger")


def get_outcomes_dir() -> Path:
    return get_runtime_data_path("outcomes")


def get_collector_scheduler_dir() -> Path:
    return get_runtime_data_path("collector_scheduler")


def get_institutional_lab_dir() -> Path:
    return get_runtime_data_path("institutional_lab")


def get_data_sources_dir() -> Path:
    return get_runtime_data_path("data_sources")


def get_calibration_reports_dir() -> Path:
    return get_runtime_data_path("calibration")


def _persistence_warning(*, configured: bool, root: Path, repository_independent: bool, render_mount_valid: bool) -> str | None:
    root_text = str(root).replace("\\", "/")
    if not configured:
        return (
            f"{RESEARCH_DATA_ROOT_ENV} is not configured; repo-local data/ fallback remains available "
            "for compatibility but is blocked for portable runtime storage."
        )
    if not repository_independent:
        return (
            f"{RESEARCH_DATA_ROOT_ENV} resolves inside the repository at {root_text}. "
            "Configure an external ResearchData root for portable runtime storage."
        )
    if not render_mount_valid:
        return f"{RESEARCH_DATA_ROOT_ENV} must point at the Render persistent disk mount /var/data when running on Render."
    return None


def get_storage_health() -> dict[str, Any]:
    root, configured, configured_via_env_var = _selected_root()
    repo_root = _repo_root().resolve()
    root_text = str(root).replace("\\", "/")
    repository_independent = not _path_is_within(root, repo_root)
    mount_anchor = _nearest_existing_anchor(root)
    mount_ok = mount_anchor is not None
    read_ok = False
    write_ok = False
    probe_error = None
    if mount_ok or root.parent.exists():
        read_ok, write_ok, probe_error = _probe_root_access(root)
    free_space_bytes, free_space_anchor = _free_space(root)
    free_space_ok = isinstance(free_space_bytes, int) and free_space_bytes > 0
    render_mount_valid = _render_mount_valid(root_text, configured)
    storage_ready = bool(configured and repository_independent and mount_ok and read_ok and write_ok and free_space_ok and render_mount_valid)
    validation_errors: list[str] = []
    if not configured:
        validation_errors.append("research_data_root_unconfigured")
    if not repository_independent:
        validation_errors.append("storage_root_inside_repository")
    if not mount_ok:
        validation_errors.append("storage_mount_unavailable")
    if not read_ok:
        validation_errors.append("storage_read_probe_failed")
    if not write_ok:
        validation_errors.append("storage_write_probe_failed")
    if not free_space_ok:
        validation_errors.append("storage_free_space_check_failed")
    if not render_mount_valid:
        validation_errors.append("render_persistent_disk_mount_invalid")
    return {
        "env_var": configured_via_env_var or AUTOMATION_DATA_DIR_ENV,
        "canonical_env_var": RESEARCH_DATA_ROOT_ENV,
        "legacy_env_var": AUTOMATION_DATA_DIR_ENV,
        "configured_via_env_var": configured_via_env_var,
        "data_dir": str(root),
        "path_normalized": root_text,
        "backend": "file",
        "configured": configured,
        "repo_local_fallback_active": not configured,
        "safe_fallback_prevented": configured,
        "repository_independent": repository_independent,
        "mount_ok": mount_ok,
        "mount_anchor": str(mount_anchor) if mount_anchor is not None else None,
        "render_persistent_disk_expected": bool(configured and root_text.startswith("/var/data")),
        "render_persistent_disk_valid": render_mount_valid,
        "persistence_warning": _persistence_warning(
            configured=configured,
            root=root,
            repository_independent=repository_independent,
            render_mount_valid=render_mount_valid,
        ),
        "read_ok": bool(read_ok),
        "write_ok": bool(write_ok),
        "probe_error": probe_error,
        "free_space_ok": free_space_ok,
        "free_space_bytes": free_space_bytes,
        "free_space_gb": round(free_space_bytes / float(1024**3), 2) if free_space_bytes is not None else None,
        "free_space_anchor": str(free_space_anchor) if free_space_anchor is not None else None,
        "storage_ready": storage_ready,
        "migration_ready": storage_ready,
        "validation_errors": validation_errors,
    }
