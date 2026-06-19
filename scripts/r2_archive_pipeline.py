from __future__ import annotations

import argparse
import gzip
import json
import subprocess
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Iterable

from src.storage.archive_manifest import (
    ArchiveManifest,
    build_archive_paths,
    build_bundle_name,
    build_manifest,
    mark_cleanup_eligible,
    mark_deletion_performed,
    mark_uploaded,
    mark_verified,
    parse_trading_date,
    read_manifest,
    validate_cleanup_gates,
    write_manifest,
)
from src.storage.r2_archive_adapter import (
    create_r2_client,
    load_r2_config_from_env,
    upload_archive,
    verify_archive_object,
)


@dataclass(slots=True)
class ArchiveLoadResult:
    records: list[dict[str, Any]] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    source_byte_count: int = 0
    skipped_invalid_json_count: int = 0
    skipped_files: list[str] = field(default_factory=list)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="R2 archive pipeline for local market data bundles.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--market", required=True)
    parser.add_argument("--trading-date", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--bundle", action="store_true")
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--cleanup-plan", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--include-pattern", default="*.json")
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--allow-delete-local-raw", action="store_true")
    parser.add_argument("--manifest-path")
    return parser.parse_args(argv)


def _is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") or part == "__pycache__" for part in path.parts)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def iter_candidate_json_files(
    input_dir: str | Path,
    *,
    output_dir: str | Path,
    include_pattern: str = "*.json",
    limit: int | None = None,
) -> list[Path]:
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    generated_roots = [output_path / "archives", output_path / "reports"]
    output_inside_input = _is_under(output_path, input_path)
    candidates: list[Path] = []
    for path in sorted(input_path.rglob("*"), key=lambda item: str(item).lower()):
        if not path.is_file():
            continue
        if _is_hidden_path(path):
            continue
        rel = path.relative_to(input_path)
        if rel.parts and rel.parts[0].lower() == "tests" and len(rel.parts) > 1 and rel.parts[1].lower() == "fixtures":
            continue
        if output_inside_input and _is_under(path, output_path):
            continue
        if any(_is_under(path, root) for root in generated_roots):
            continue
        if not fnmatch(path.name, include_pattern):
            continue
        candidates.append(path)
        if limit is not None and len(candidates) >= limit:
            break
    return candidates


def _safe_relpath(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path.resolve()).replace("\\", "/")


def _read_json_payload(path: Path) -> tuple[Any | None, bool]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), True
    except Exception:
        return None, False


def _records_from_payload(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    return [payload]


def load_json_records(
    *,
    input_dir: str | Path,
    output_dir: str | Path,
    environment: str,
    source: str,
    market: str,
    trading_date: str,
    archive_id: str,
    include_pattern: str = "*.json",
    limit: int | None = None,
) -> ArchiveLoadResult:
    input_path = Path(input_dir)
    candidates = iter_candidate_json_files(input_path, output_dir=output_dir, include_pattern=include_pattern, limit=limit)
    load_result = ArchiveLoadResult()
    load_result.source_files = [_safe_relpath(path, input_path) for path in candidates]
    load_result.source_byte_count = sum(path.stat().st_size for path in candidates)

    for path in candidates:
        payload, ok = _read_json_payload(path)
        rel = _safe_relpath(path, input_path)
        if not ok:
            load_result.skipped_invalid_json_count += 1
            load_result.skipped_files.append(rel)
            continue
        for item in _records_from_payload(payload):
            if isinstance(item, dict):
                record = dict(item)
            else:
                record = {"value": item}
            record.update(
                {
                    "_source_file": rel,
                    "_archive_id": archive_id,
                    "_trading_date": trading_date,
                    "_source": source,
                    "_market": market,
                    "_environment": environment,
                }
            )
            load_result.records.append(record)
    return load_result


def write_archive(
    archive_path: str | Path,
    records: Iterable[dict[str, Any]],
) -> Path:
    archive_file = Path(archive_path)
    archive_file.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(archive_file, "wt", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    return archive_file


def _archive_id_for_args(args: argparse.Namespace, source_files: list[str]) -> str:
    seed = "|".join(
        [
            args.environment,
            args.source,
            args.market,
            parse_trading_date(args.trading_date).isoformat(),
            *sorted(source_files),
        ]
    )
    import uuid

    return uuid.uuid5(uuid.NAMESPACE_URL, seed).hex


def _preview_source_files(args: argparse.Namespace) -> tuple[list[Path], list[str], str]:
    candidates = iter_candidate_json_files(
        args.input_dir,
        output_dir=args.output_dir,
        include_pattern=args.include_pattern,
        limit=args.limit,
    )
    source_files = [_safe_relpath(path, Path(args.input_dir)) for path in candidates]
    archive_id = _archive_id_for_args(args, source_files)
    return candidates, source_files, archive_id


def _build_paths(args: argparse.Namespace, archive_id: str) -> tuple[Path, Path, str]:
    bundle_name = build_bundle_name(args.source, args.market, args.trading_date)
    paths = build_archive_paths(
        args.output_dir,
        args.environment,
        args.source,
        args.market,
        args.trading_date,
        archive_id,
        bundle_name,
    )
    return Path(paths.local_archive_path), Path(paths.manifest_path), paths.r2_object_key


def run_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    _, source_files, archive_id = _preview_source_files(args)
    load_result = load_json_records(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        environment=args.environment,
        source=args.source,
        market=args.market,
        trading_date=parse_trading_date(args.trading_date).isoformat(),
        archive_id=archive_id,
        include_pattern=args.include_pattern,
        limit=args.limit,
    )
    return {
        "mode": "dry-run",
        "archive_id": archive_id,
        "source_file_count": len(source_files),
        "record_count": len(load_result.records),
        "skipped_invalid_json_count": load_result.skipped_invalid_json_count,
        "skipped_files": load_result.skipped_files,
    }


def _build_manifest_from_load(
    args: argparse.Namespace,
    load_result: ArchiveLoadResult,
    *,
    archive_id: str,
    archive_path: Path | None = None,
) -> ArchiveManifest:
    archive_path = archive_path or _build_paths(args, archive_id)[0]
    return build_manifest(
        environment=args.environment,
        source=args.source,
        market=args.market,
        trading_date=parse_trading_date(args.trading_date),
        output_dir=args.output_dir,
        source_files=load_result.source_files,
        source_byte_count=load_result.source_byte_count,
        skipped_invalid_json_count=load_result.skipped_invalid_json_count,
        skipped_files=load_result.skipped_files,
        archive_path=archive_path if archive_path.is_file() else None,
        archive_id=archive_id,
    )


def run_bundle(args: argparse.Namespace) -> tuple[ArchiveManifest, Path]:
    _, _, archive_id = _preview_source_files(args)
    load_result = load_json_records(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        environment=args.environment,
        source=args.source,
        market=args.market,
        trading_date=parse_trading_date(args.trading_date).isoformat(),
        archive_id=archive_id,
        include_pattern=args.include_pattern,
        limit=args.limit,
    )
    archive_path, manifest_path, _ = _build_paths(args, archive_id)
    if not args.manifest_only:
        write_archive(archive_path, load_result.records)
    manifest = _build_manifest_from_load(args, load_result, archive_id=archive_id, archive_path=archive_path if archive_path.is_file() else None)
    write_manifest(manifest, manifest_path)
    return manifest, manifest_path


def run_upload(args: argparse.Namespace, manifest: ArchiveManifest, manifest_path: Path, archive_path: Path) -> ArchiveManifest:
    config = load_r2_config_from_env()
    client = create_r2_client(config)
    result = upload_archive(client, config, archive_path, manifest.r2_object_key)
    manifest = mark_uploaded(manifest, uploaded_at_utc=None, r2_bucket_alias=result.bucket_alias)
    write_manifest(manifest, manifest_path)
    return manifest


def run_verify(
    args: argparse.Namespace,
    manifest: ArchiveManifest,
    manifest_path: Path,
    archive_path: Path,
) -> ArchiveManifest:
    config = load_r2_config_from_env()
    client = create_r2_client(config)
    result = verify_archive_object(client, config, manifest.r2_object_key, expected_byte_count=archive_path.stat().st_size)
    if result.verified:
        manifest = mark_verified(manifest)
    else:
        manifest = mark_verified(manifest, verification_status="not_verified")
    write_manifest(manifest, manifest_path)
    return manifest


def _cleanup_plan_checks(manifest: ArchiveManifest, input_dir: str | Path) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if manifest.upload_status != "uploaded":
        reasons.append("upload_status must be uploaded")
    if manifest.verification_status != "verified":
        reasons.append("verification_status must be verified")
    if not manifest.source_files:
        reasons.append("source_files must not be empty")
    for source_item in manifest.source_files:
        source_path = Path(source_item)
        candidate = source_path if source_path.is_absolute() else (Path(input_dir) / source_path)
        candidate = candidate.resolve()
        if not _is_under(candidate, Path(input_dir)):
            reasons.append(f"source file outside input dir: {source_item}")
            continue
        rel = candidate.relative_to(Path(input_dir).resolve())
        if len(rel.parts) >= 2 and rel.parts[0].lower() == "tests" and rel.parts[1].lower() == "fixtures":
            reasons.append(f"source file under tests/fixtures: {source_item}")
        if candidate.name.lower().endswith((".py", ".pyi", ".ps1", ".sh", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
            reasons.append(f"source file is code: {source_item}")
        if candidate.name.lower().endswith((".jsonl.gz", ".json.gz", ".tar.gz", ".zip")):
            reasons.append(f"source file is archive-like: {source_item}")
        if "manifest" in candidate.name.lower():
            reasons.append(f"source file is manifest-like: {source_item}")
        if not candidate.exists():
            reasons.append(f"source file missing: {source_item}")
    return (not reasons), reasons


def run_cleanup_plan(args: argparse.Namespace, manifest: ArchiveManifest, manifest_path: Path) -> ArchiveManifest:
    eligible, _ = _cleanup_plan_checks(manifest, args.input_dir)
    if eligible:
        manifest = mark_cleanup_eligible(manifest, eligible=True)
        write_manifest(manifest, manifest_path)
    return manifest


def _find_git_root(path: Path) -> Path | None:
    for candidate in [path.resolve(), *path.resolve().parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def _git_check_ignore(path: Path) -> bool | None:
    root = _find_git_root(path)
    if root is None:
        return True
    rel = path.resolve().relative_to(root)
    proc = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", str(rel)],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def _git_check_tracked(path: Path) -> bool | None:
    root = _find_git_root(path)
    if root is None:
        return False
    rel = path.resolve().relative_to(root)
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", str(rel)],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def _is_local_only(path: Path) -> bool | None:
    root = _find_git_root(path)
    if root is None:
        return True
    ignored = _git_check_ignore(path)
    if ignored is True:
        return True
    tracked = _git_check_tracked(path)
    if tracked is False:
        return True
    if tracked is True:
        return False
    return None


def run_cleanup(
    args: argparse.Namespace,
    manifest: ArchiveManifest,
    manifest_path: Path,
) -> ArchiveManifest:
    manifest = mark_cleanup_eligible(manifest, eligible=manifest.deletion_eligible, deletion_allowed_by_user=args.allow_delete_local_raw)
    ok, reasons = validate_cleanup_gates(
        manifest,
        input_dir=args.input_dir,
        cleanup_mode=True,
        allow_delete_local_raw=args.allow_delete_local_raw,
        tracked_file_checker=lambda path: _git_check_tracked(path) is True,
        local_only_checker=_is_local_only,
    )
    if not ok:
        manifest = write_manifest(manifest, manifest_path)
        return manifest

    deleted_count = 0
    deleted_bytes = 0
    input_root = Path(args.input_dir).resolve()
    for source_item in manifest.source_files:
        source_path = Path(source_item)
        candidate = source_path if source_path.is_absolute() else (input_root / source_path)
        candidate = candidate.resolve()
        if not candidate.exists() or not candidate.is_file():
            continue
        if not _is_under(candidate, input_root):
            continue
        if candidate.name.lower().endswith((".jsonl.gz", ".json.gz", ".tar.gz", ".zip")):
            continue
        if "manifest" in candidate.name.lower():
            continue
        if len(candidate.relative_to(input_root).parts) >= 2 and candidate.relative_to(input_root).parts[0].lower() == "tests" and candidate.relative_to(input_root).parts[1].lower() == "fixtures":
            continue
        deleted_bytes += candidate.stat().st_size
        candidate.unlink()
        deleted_count += 1

    manifest = mark_deletion_performed(
        manifest,
        deleted_source_file_count=deleted_count,
        deleted_source_byte_count=deleted_bytes,
    )
    write_manifest(manifest, manifest_path)
    return manifest


def _resolve_manifest_path(args: argparse.Namespace, manifest: ArchiveManifest | None = None) -> Path:
    if args.manifest_path:
        return Path(args.manifest_path)
    if manifest is not None:
        return Path(args.output_dir) / "reports" / "archive_manifests" / f"{manifest.archive_id}.json"
    _, _, archive_id = _preview_source_files(args)
    return Path(args.output_dir) / "reports" / "archive_manifests" / f"{archive_id}.json"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dry_run:
        run_dry_run(args)
        return 0

    if not any([args.bundle, args.manifest_only, args.upload, args.verify, args.cleanup_plan, args.cleanup]):
        return 0

    manifest: ArchiveManifest | None = None
    manifest_path: Path | None = None
    archive_path: Path | None = None

    if args.bundle or args.manifest_only:
        manifest, manifest_path = run_bundle(args)
        archive_path, _, _ = _build_paths(args, manifest.archive_id)

    if args.manifest_path:
        manifest_path = Path(args.manifest_path)
        if manifest_path.exists():
            manifest = read_manifest(manifest_path)
            archive_path = Path(manifest.local_archive_path)

    if manifest is None or manifest_path is None:
        if args.upload or args.verify or args.cleanup_plan or args.cleanup:
            manifest_path = _resolve_manifest_path(args)
            if not manifest_path.exists():
                raise FileNotFoundError("Manifest file is required before upload, verify, or cleanup.")
            manifest = read_manifest(manifest_path)
            archive_path = Path(manifest.local_archive_path)
        else:
            archive_id = _archive_id_for_args(args, [])
            manifest_path = _resolve_manifest_path(args)
            archive_path, _, _ = _build_paths(args, archive_id)
            manifest = build_manifest(
                environment=args.environment,
                source=args.source,
                market=args.market,
                trading_date=parse_trading_date(args.trading_date),
                output_dir=args.output_dir,
                source_files=[],
                source_byte_count=0,
                archive_path=archive_path if archive_path.is_file() else None,
                archive_id=archive_id,
            )

    if args.upload:
        if archive_path is None or not archive_path.exists():
            raise FileNotFoundError("Archive file is required before upload.")
        manifest = run_upload(args, manifest, manifest_path, archive_path)

    if args.verify:
        if archive_path is None or not archive_path.exists():
            raise FileNotFoundError("Archive file is required before verify.")
        manifest = run_verify(args, manifest, manifest_path, archive_path)

    if args.cleanup_plan:
        manifest = run_cleanup_plan(args, manifest, manifest_path)

    if args.cleanup:
        manifest = run_cleanup(args, manifest, manifest_path)

    if manifest_path is not None and not manifest_path.exists():
        write_manifest(manifest, manifest_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
