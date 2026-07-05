from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any

try:  # pragma: no cover - optional until runtime dependency is installed
    import boto3  # type: ignore
except Exception:  # pragma: no cover - module must still import cleanly in tests
    boto3 = None  # type: ignore


@dataclass(slots=True)
class R2ArchiveConfig:
    account_id: str
    access_key_id: str = field(repr=False)
    secret_access_key: str = field(repr=False)
    bucket_name: str
    endpoint_url: str

    @property
    def bucket_alias(self) -> str:
        return self.bucket_name or "not_configured"


@dataclass(slots=True)
class R2ArchiveUploadResult:
    bucket_alias: str
    bucket_name: str
    object_key: str
    archive_byte_count: int
    etag: str | None = None
    response_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class R2ArchiveVerificationResult:
    bucket_alias: str
    bucket_name: str
    object_key: str
    verified: bool
    content_length: int | None = None
    etag: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def load_r2_config_from_env() -> R2ArchiveConfig:
    required_keys = [
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
        "R2_ENDPOINT_URL",
    ]
    missing = [key for key in required_keys if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing required R2 environment variables: {', '.join(missing)}")
    return R2ArchiveConfig(
        account_id=os.environ["R2_ACCOUNT_ID"],
        access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        bucket_name=os.environ["R2_BUCKET_NAME"],
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
    )


def create_r2_client(config: R2ArchiveConfig) -> Any:
    if boto3 is None:  # pragma: no cover - runtime dependency absent in this environment
        raise RuntimeError("boto3 is required to create the R2 archive client")
    return boto3.client(
        "s3",
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        endpoint_url=config.endpoint_url,
    )


def upload_archive(
    client: Any,
    config: R2ArchiveConfig,
    archive_path: str | Path,
    object_key: str,
) -> R2ArchiveUploadResult:
    archive_file = Path(archive_path)
    archive_byte_count = archive_file.stat().st_size
    if hasattr(client, "upload_file"):
        client.upload_file(str(archive_file), config.bucket_name, object_key)
    elif hasattr(client, "put_object"):
        client.put_object(Bucket=config.bucket_name, Key=object_key, Body=archive_file.read_bytes())
    else:  # pragma: no cover - defensive path for unusual fakes
        raise AttributeError("Client does not support upload_file or put_object")
    return R2ArchiveUploadResult(
        bucket_alias=config.bucket_alias,
        bucket_name=config.bucket_name,
        object_key=object_key,
        archive_byte_count=archive_byte_count,
    )


def verify_archive_object(
    client: Any,
    config: R2ArchiveConfig,
    object_key: str,
    *,
    expected_byte_count: int | None = None,
) -> R2ArchiveVerificationResult:
    try:
        response = client.head_object(Bucket=config.bucket_name, Key=object_key)
    except Exception as exc:  # pragma: no cover - defensive for client failures
        return R2ArchiveVerificationResult(
            bucket_alias=config.bucket_alias,
            bucket_name=config.bucket_name,
            object_key=object_key,
            verified=False,
            error=str(exc),
        )

    content_length = response.get("ContentLength")
    etag = response.get("ETag")
    metadata = dict(response)
    verified = True
    error = None
    if expected_byte_count is not None and content_length is None:
        verified = False
        error = "content length missing from remote object metadata"
    elif expected_byte_count is not None and content_length is not None and int(content_length) != int(expected_byte_count):
        verified = False
        error = f"content length mismatch: expected {expected_byte_count}, got {content_length}"
    return R2ArchiveVerificationResult(
        bucket_alias=config.bucket_alias,
        bucket_name=config.bucket_name,
        object_key=object_key,
        verified=verified,
        content_length=int(content_length) if content_length is not None else None,
        etag=etag,
        metadata=metadata,
        error=error,
    )
