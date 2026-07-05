from __future__ import annotations

import os
from pathlib import Path
from typing import Any


AUTOMATION_DATA_DIR_ENV = "AUTOMATION_DATA_DIR"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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


def _configured_root() -> Path | None:
    raw = os.getenv(AUTOMATION_DATA_DIR_ENV)
    if raw is None or not raw.strip():
        return None
    return Path(raw.strip()).expanduser()


def get_automation_data_dir() -> Path:
    configured = _configured_root()
    root = configured if configured is not None else (_repo_root() / "data")
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
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


def _persistence_warning(configured: bool, root: Path) -> str | None:
    render = _is_render_runtime()
    root_text = str(root).replace("\\", "/")
    if not configured:
        return (
            f"{AUTOMATION_DATA_DIR_ENV} is not configured; using repo-local data/ fallback. "
            "On Render this is likely ephemeral."
        )
    if render and root_text != "/var/data" and not root_text.startswith("/var/data/"):
        return f"{AUTOMATION_DATA_DIR_ENV} is set outside expected Render persistent disk mount /var/data."
    return None


def get_storage_health() -> dict[str, Any]:
    configured = _configured_root() is not None
    root = get_automation_data_dir()
    read_ok = False
    write_ok = False
    probe = root / ".automation_data_dir_probe"
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
        write_ok = True
        read_ok = probe.read_text(encoding="utf-8") == "ok"
    except Exception:
        read_ok = False
        write_ok = False
    finally:
        try:
            probe.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            pass
    return {
        "env_var": AUTOMATION_DATA_DIR_ENV,
        "data_dir": str(root),
        "backend": "file",
        "configured": configured,
        "render_persistent_disk_expected": bool(configured and str(root).replace("\\", "/").startswith("/var/data")),
        "persistence_warning": _persistence_warning(configured, root),
        "read_ok": bool(read_ok),
        "write_ok": bool(write_ok),
    }
