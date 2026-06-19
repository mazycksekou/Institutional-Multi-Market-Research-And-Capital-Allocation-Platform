from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date as date_cls, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
import uuid


APPROVED_ARCHIVE_SUFFIXES = {".json", ".jsonl", ".jsonl.gz", ".json.gz"}
ARCHIVE_SUFFIXES = {".jsonl.gz", ".json.gz", ".tar.gz", ".zip"}
CODE_SUFFIXES = {".py", ".pyi", ".ps1", ".sh", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}


@dataclass(slots=True)
class ArchivePaths:
    local_archive_path: str
    manifest_path: str
    r2_object_key: str
    bundle_name: str


@dataclass(slots=True)
class ArchiveManifest:
    archive_id: str
    environment: str
    source: str
    market: str
    trading_date: str
    archive_format: str
    local_archive_path: str
    r2_bucket_alias: str = "not_configured"
    r2_object_key: str = ""
    source_file_count: int = 0
    source_byte_count: int = 0
    archive_byte_count: int = 0
    checksum_algorithm: str = "sha256"
    checksum: str = ""
    created_at_utc: str = ""
    uploaded_at_utc: str | None = None
    upload_status: str = "not_uploaded"
    verification_status: str = "not_verified"
    deletion_eligible: bool = False
    deletion_performed: bool = False
    deletion_allowed_by_user: bool = False
    deletion_completed_at_utc: str | None = None
    deleted_source_file_count: int = 0
    deleted_source_byte_count: int = 0
    notes: str = "10K8ZF7 R2 archive pipeline"
    source_files: list[str] = field(default_factory=list)
    skipped_invalid_json_count: int = 0
    skipped_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive_id": self.archive_id,
            "environment": self.environment,
            "source": self.source,
            "market": self.market,
            "trading_date": self.trading_date,
            "archive_format": self.archive_format,
            "local_archive_path": self.local_archive_path,
            "r2_bucket_alias": self.r2_bucket_alias,
            "r2_object_key": self.r2_object_key,
            "source_file_count": self.source_file_count,
            "source_byte_count": self.source_byte_count,
            "archive_byte_count": self.archive_byte_count,
            "checksum_algorithm": self.checksum_algorithm,
            "checksum": self.checksum,
            "created_at_utc": self.created_at_utc,
            "uploaded_at_utc": self.uploaded_at_utc,
            "upload_status": self.upload_status,
            "verification_status": self.verification_status,
            "deletion_eligible": self.deletion_eligible,
            "deletion_performed": self.deletion_performed,
            "deletion_allowed_by_user": self.deletion_allowed_by_user,
            "deletion_completed_at_utc": self.deletion_completed_at_utc,
            "deleted_source_file_count": self.deleted_source_file_count,
            "deleted_source_byte_count": self.deleted_source_byte_count,
            "notes": self.notes,
            "source_files": list(self.source_files),
            "skipped_invalid_json_count": self.skipped_invalid_json_count,
            "skipped_files": list(self.skipped_files),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ArchiveManifest":
        return cls(
            archive_id=str(payload.get("archive_id", "")),
            environment=str(payload.get("environment", "")),
            source=str(payload.get("source", "")),
            market=str(payload.get("market", "")),
            trading_date=str(payload.get("trading_date", "")),
            archive_format=str(payload.get("archive_format", "jsonl.gz")),
            local_archive_path=str(payload.get("local_archive_path", "")),
            r2_bucket_alias=str(payload.get("r2_bucket_alias", "not_configured")),
            r2_object_key=str(payload.get("r2_object_key", "")),
            source_file_count=int(payload.get("source_file_count", 0) or 0),
            source_byte_count=int(payload.get("source_byte_count", 0) or 0),
            archive_byte_count=int(payload.get("archive_byte_count", 0) or 0),
            checksum_algorithm=str(payload.get("checksum_algorithm", "sha256")),
            checksum=str(payload.get("checksum", "")),
            created_at_utc=str(payload.get("created_at_utc", "")),
            uploaded_at_utc=payload.get("uploaded_at_utc"),
            upload_status=str(payload.get("upload_status", "not_uploaded")),
            verification_status=str(payload.get("verification_status", "not_verified")),
            deletion_eligible=bool(payload.get("deletion_eligible", False)),
            deletion_performed=bool(payload.get("deletion_performed", False)),
            deletion_allowed_by_user=bool(payload.get("deletion_allowed_by_user", False)),
            deletion_completed_at_utc=payload.get("deletion_completed_at_utc"),
            deleted_source_file_count=int(payload.get("deleted_source_file_count", 0) or 0),
            deleted_source_byte_count=int(payload.get("deleted_source_byte_count", 0) or 0),
            notes=str(payload.get("notes", "10K8ZF7 R2 archive pipeline")),
            source_files=[str(item) for item in payload.get("source_files", []) or []],
            skipped_invalid_json_count=int(payload.get("skipped_invalid_json_count", 0) or 0),
            skipped_files=[str(item) for item in payload.get("skipped_files", []) or []],
        )


def sanitize_slug(value: str) -> str:
    chars: list[str] = []
    last_was_dash = False
    for char in str(value).strip().lower():
        if char.isalnum():
            chars.append(char)
            last_was_dash = False
        else:
            if not last_was_dash:
                chars.append("-")
                last_was_dash = True
    slug = "".join(chars).strip("-")
    return slug or "unknown"


def parse_trading_date(value: str | date_cls | datetime) -> date_cls:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date_cls):
        return value
    text = str(value).strip()
    return date_cls.fromisoformat(text)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_bundle_name(source: str, market: str, trading_date: str | date_cls | datetime) -> str:
    trading_day = parse_trading_date(trading_date)
    return f"{sanitize_slug(source)}_{sanitize_slug(market)}_{trading_day:%Y-%m-%d}"


def build_r2_object_key(
    environment: str,
    source: str,
    market: str,
    trading_date: str | date_cls | datetime,
    bundle_name: str,
    ext: str = "jsonl.gz",
) -> str:
    trading_day = parse_trading_date(trading_date)
    return (
        f"market-data/{sanitize_slug(environment)}/{sanitize_slug(source)}/"
        f"{sanitize_slug(market)}/{trading_day:%Y/%m/%d}/{bundle_name}.{ext}"
    )


def build_archive_paths(
    output_dir: str | Path,
    environment: str,
    source: str,
    market: str,
    trading_date: str | date_cls | datetime,
    archive_id: str,
    bundle_name: str,
    archive_format: str = "jsonl.gz",
) -> ArchivePaths:
    output_path = Path(output_dir)
    trading_day = parse_trading_date(trading_date)
    local_archive_path = (
        output_path
        / "archives"
        / "local"
        / sanitize_slug(source)
        / sanitize_slug(market)
        / f"{trading_day:%Y}"
        / f"{trading_day:%m}"
        / f"{trading_day:%d}"
        / f"{bundle_name}.{archive_format}"
    )
    manifest_path = output_path / "reports" / "archive_manifests" / f"{archive_id}.json"
    object_key = build_r2_object_key(environment, source, market, trading_date, bundle_name, ext=archive_format)
    return ArchivePaths(
        local_archive_path=str(local_archive_path),
        manifest_path=str(manifest_path),
        r2_object_key=object_key,
        bundle_name=bundle_name,
    )


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _archive_id(
    environment: str,
    source: str,
    market: str,
    trading_date: str | date_cls | datetime,
    source_files: Sequence[str],
) -> str:
    seed = "|".join(
        [
            sanitize_slug(environment),
            sanitize_slug(source),
            sanitize_slug(market),
            parse_trading_date(trading_date).isoformat(),
            *sorted(str(item) for item in source_files),
        ]
    )
    return uuid.uuid5(uuid.NAMESPACE_URL, seed).hex


def build_manifest(
    *,
    environment: str,
    source: str,
    market: str,
    trading_date: str | date_cls | datetime,
    output_dir: str | Path,
    source_files: Sequence[str],
    source_byte_count: int,
    skipped_invalid_json_count: int = 0,
    skipped_files: Sequence[str] | None = None,
    archive_path: str | Path | None = None,
    archive_format: str = "jsonl.gz",
    r2_bucket_alias: str = "not_configured",
    archive_id: str | None = None,
) -> ArchiveManifest:
    bundle_name = build_bundle_name(source, market, trading_date)
    archive_id = archive_id or _archive_id(environment, source, market, trading_date, source_files)
    paths = build_archive_paths(output_dir, environment, source, market, trading_date, archive_id, bundle_name, archive_format)
    archive_file = Path(archive_path or paths.local_archive_path)
    archive_byte_count = archive_file.stat().st_size if archive_file.is_file() else 0
    checksum = sha256_file(archive_file) if archive_file.is_file() else ""
    return ArchiveManifest(
        archive_id=archive_id,
        environment=sanitize_slug(environment),
        source=sanitize_slug(source),
        market=sanitize_slug(market),
        trading_date=parse_trading_date(trading_date).isoformat(),
        archive_format=archive_format,
        local_archive_path=str(archive_file),
        r2_bucket_alias=r2_bucket_alias or "not_configured",
        r2_object_key=paths.r2_object_key,
        source_file_count=len(source_files),
        source_byte_count=int(source_byte_count),
        archive_byte_count=int(archive_byte_count),
        checksum_algorithm="sha256",
        checksum=checksum,
        created_at_utc=utc_now_iso(),
        uploaded_at_utc=None,
        upload_status="not_uploaded",
        verification_status="not_verified",
        deletion_eligible=False,
        deletion_performed=False,
        deletion_allowed_by_user=False,
        deletion_completed_at_utc=None,
        deleted_source_file_count=0,
        deleted_source_byte_count=0,
        notes="10K8ZF7 R2 archive pipeline",
        source_files=[str(item) for item in source_files],
        skipped_invalid_json_count=int(skipped_invalid_json_count),
        skipped_files=[str(item) for item in (skipped_files or [])],
    )


def write_manifest(manifest: ArchiveManifest, path: str | Path) -> Path:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def read_manifest(path: str | Path) -> ArchiveManifest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest file must contain a JSON object.")
    return ArchiveManifest.from_dict(payload)


def mark_uploaded(
    manifest: ArchiveManifest,
    *,
    uploaded_at_utc: str | None = None,
    r2_bucket_alias: str | None = None,
) -> ArchiveManifest:
    return replace(
        manifest,
        upload_status="uploaded",
        uploaded_at_utc=uploaded_at_utc or utc_now_iso(),
        r2_bucket_alias=r2_bucket_alias or manifest.r2_bucket_alias or "not_configured",
    )


def mark_verified(
    manifest: ArchiveManifest,
    *,
    verification_status: str = "verified",
) -> ArchiveManifest:
    return replace(manifest, verification_status=verification_status)


def mark_cleanup_eligible(
    manifest: ArchiveManifest,
    *,
    eligible: bool = True,
    deletion_allowed_by_user: bool | None = None,
) -> ArchiveManifest:
    updates: dict[str, Any] = {"deletion_eligible": eligible}
    if deletion_allowed_by_user is not None:
        updates["deletion_allowed_by_user"] = deletion_allowed_by_user
    return replace(manifest, **updates)


def mark_deletion_performed(
    manifest: ArchiveManifest,
    *,
    deleted_source_file_count: int,
    deleted_source_byte_count: int,
    deletion_completed_at_utc: str | None = None,
) -> ArchiveManifest:
    return replace(
        manifest,
        deletion_performed=True,
        deletion_completed_at_utc=deletion_completed_at_utc or utc_now_iso(),
        deleted_source_file_count=int(deleted_source_file_count),
        deleted_source_byte_count=int(deleted_source_byte_count),
        deletion_allowed_by_user=True,
    )


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _is_source_code_file(path: Path) -> bool:
    return path.suffix.lower() in CODE_SUFFIXES


def _is_archive_file(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def _is_manifest_file(path: Path) -> bool:
    lower = path.name.lower()
    return "manifest" in lower or lower.endswith(".manifest.json")


def validate_cleanup_gates(
    manifest: ArchiveManifest,
    *,
    input_dir: str | Path,
    cleanup_mode: bool = False,
    allow_delete_local_raw: bool = False,
    tracked_file_checker: Callable[[Path], bool] | None = None,
    local_only_checker: Callable[[Path], bool | None] | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    input_path = Path(input_dir)

    if not cleanup_mode:
        reasons.append("cleanup mode is not enabled")
    if not allow_delete_local_raw:
        reasons.append("allow-delete-local-raw is not enabled")
    if manifest.upload_status != "uploaded":
        reasons.append("upload_status must be uploaded")
    if manifest.verification_status != "verified":
        reasons.append("verification_status must be verified")
    if not manifest.deletion_eligible:
        reasons.append("deletion_eligible must be true")
    if manifest.deletion_performed:
        reasons.append("deletion_performed must be false")
    if not manifest.deletion_allowed_by_user:
        reasons.append("deletion_allowed_by_user must be true")
    if not manifest.source_files:
        reasons.append("source_files must not be empty")

    for source_item in manifest.source_files:
        source_path = Path(source_item)
        candidate = source_path if source_path.is_absolute() else (input_path / source_path)
        candidate = candidate.resolve()
        if not _is_relative_to(candidate, input_path):
            reasons.append(f"source file outside input dir: {source_item}")
            continue
        rel = candidate.relative_to(input_path.resolve())
        if len(rel.parts) >= 2 and rel.parts[0].lower() == "tests" and rel.parts[1].lower() == "fixtures":
            reasons.append(f"source file under tests/fixtures: {source_item}")
        if _is_source_code_file(candidate):
            reasons.append(f"source file is code: {source_item}")
        if _is_archive_file(candidate):
            reasons.append(f"source file is archive-like: {source_item}")
        if _is_manifest_file(candidate):
            reasons.append(f"source file is manifest-like: {source_item}")
        if not candidate.exists():
            reasons.append(f"source file missing: {source_item}")
        if tracked_file_checker is not None and tracked_file_checker(candidate):
            reasons.append(f"source file is tracked: {source_item}")
        if local_only_checker is not None:
            local_only = local_only_checker(candidate)
            if local_only is False:
                reasons.append(f"source file is not local-only: {source_item}")

    return (not reasons), reasons

