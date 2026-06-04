from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import get_data_sources_dir, resolve_base_data_dir
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


MLB_MODULE = "baseball_mlb"
MLB_DATA_ROOT_NAME = "mlb_open_data"


def mlb_root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / MLB_DATA_ROOT_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def mlb_report_root(*, base_data_dir: str | Path | None = None, subdir: str) -> Path:
    root = mlb_root(base_data_dir) / subdir
    root.mkdir(parents=True, exist_ok=True)
    return root


def mlb_validated_root(source_id: str, base_data_dir: str | Path | None = None) -> Path:
    root = mlb_root(base_data_dir) / "validated" / sanitize_filename(source_id)
    root.mkdir(parents=True, exist_ok=True)
    return root


def mlb_rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def mlb_read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def mlb_atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def mlb_atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def mlb_safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {**SAFETY_FIELDS, **payload, "raw_payload_included": False, "raw_html_persisted": False, "secrets_included": False}

