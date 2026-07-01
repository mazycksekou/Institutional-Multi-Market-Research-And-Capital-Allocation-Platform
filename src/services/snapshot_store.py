from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.services.scheduler_config import SCHEMA_VERSION, redact_secrets, sanitize_filename, utc_now_iso


class SnapshotStore:
    def __init__(self, config: dict[str, Any]) -> None:
        self._base_dir = Path(config["paths"]["snapshots"])
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, namespace: str, key: str) -> Path:
        folder = self._base_dir / sanitize_filename(namespace)
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{sanitize_filename(key)}.json"

    def save_snapshot(self, namespace: str, key: str, payload: Any) -> dict[str, Any]:
        now = utc_now_iso()
        wrapper = {
            "schema_version": SCHEMA_VERSION,
            "saved_at": now,
            "received_at": now,
            "namespace": namespace,
            "key": key,
            "payload": redact_secrets(payload),
        }
        path = self._path_for(namespace, key)
        path.write_text(json.dumps(wrapper, indent=2, sort_keys=True), encoding="utf-8")
        return wrapper

    def load_snapshot(self, namespace: str, key: str) -> dict[str, Any] | None:
        path = self._path_for(namespace, key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def load_latest_snapshot(self, namespace: str, key: str) -> dict[str, Any] | None:
        return self.load_snapshot(namespace, key)

    def list_snapshots(self, namespace: str) -> list[dict[str, Any]]:
        folder = self._base_dir / sanitize_filename(namespace)
        if not folder.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in sorted(folder.glob("*.json")):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return items

    @staticmethod
    def diff_snapshots(previous: dict[str, Any] | None, current: dict[str, Any] | None) -> dict[str, Any]:
        previous_payload = (previous or {}).get("payload", previous or {})
        current_payload = (current or {}).get("payload", current or {})
        changed_keys = []
        all_keys = sorted(set(previous_payload) | set(current_payload))
        for key in all_keys:
            if previous_payload.get(key) != current_payload.get(key):
                changed_keys.append(key)
        return {
            "changed": bool(changed_keys),
            "changed_keys": changed_keys,
            "previous_count": len(previous_payload) if isinstance(previous_payload, dict) else 0,
            "current_count": len(current_payload) if isinstance(current_payload, dict) else 0,
        }


def save_snapshot(category: str, key: str, payload: Any, config: dict[str, Any]) -> dict[str, Any]:
    return SnapshotStore(config).save_snapshot(category, key, payload)


def load_latest_snapshot(category: str, key: str, config: dict[str, Any]) -> dict[str, Any] | None:
    return SnapshotStore(config).load_latest_snapshot(category, key)


def diff_snapshots(previous: dict[str, Any] | None, current: dict[str, Any] | None) -> dict[str, Any]:
    return SnapshotStore.diff_snapshots(previous, current)
